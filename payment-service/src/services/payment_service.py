import contextlib
import logging
import uuid
from typing import TYPE_CHECKING, Any

import redis.asyncio as redis_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.datatype import uuid7
from src.engines.rabbitmq import (
    publish_payment_failed,
    publish_payment_refunded,
    publish_payment_succeeded,
)
from src.engines.redis import check_idempotency
from src.enums.payment_status import (
    PAYMENT_STATE_MACHINE,
    PaymentMethod,
    PaymentStatus,
    TransactionType,
)
from src.exceptions import ConflictError, NotFoundError
from src.models.payment import Payment, Transaction
from src.patterns.gateway_registry import PaymentGatewayRegistry
from src.patterns.payload_builder import PaymentPayloadBuilder
from src.patterns.state_machine import InvalidTransitionError
from src.repositories.payment_repo import PaymentRepo

if TYPE_CHECKING:
    from src.patterns.gateway_strategy import BasePaymentGateway

logger = logging.getLogger(__name__)


class PaymentService:
    """Core service for payment operations."""

    def __init__(
        self,
        payment_repo: PaymentRepo,
        gateway_registry: PaymentGatewayRegistry,
        redis_client: redis_asyncio.Redis,
        payload_builder: PaymentPayloadBuilder,
    ) -> None:
        self._repo = payment_repo
        self._registry = gateway_registry
        self._redis = redis_client
        self._payload_builder = payload_builder

    async def create_payment(
        self,
        *,
        session: AsyncSession,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
        amount: int,
        currency: str,
        payment_method: PaymentMethod,
        idempotency_key: str,
    ) -> Payment:
        """Create a payment and process it through the appropriate gateway."""
        is_new = await check_idempotency(self._redis, idempotency_key)
        if not is_new:
            existing = await self._repo.get_by_idempotency_key(
                session=session, key=idempotency_key
            )
            if existing:
                return existing
            msg = f"Idempotency key conflict but no payment found: {idempotency_key}"
            raise ConflictError(msg)

        gateway: BasePaymentGateway = self._registry.get_gateway(payment_method)

        payment = Payment(
            id=uuid7(),
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            payment_method=payment_method.value,
            gateway=payment_method.value.lower(),
            idempotency_key=idempotency_key,
        )
        payment = await self._repo.create(session=session, payment=payment)

        try:
            await self._transition_status(
                session=session, payment=payment, new_status=PaymentStatus.PROCESSING
            )

            result = await gateway.create_payment(
                amount=amount,
                currency=currency,
                order_id=str(order_id),
            )

            payment.gateway_payment_id = result["gateway_payment_id"]

            if result["status"] in ("succeeded", "pending"):
                if result["status"] == "succeeded":
                    payment = await self._transition_status(
                        session=session,
                        payment=payment,
                        new_status=PaymentStatus.SUCCEEDED,
                    )
                    await self._publish_event(
                        "succeeded",
                        self._payload_builder.build_succeeded(payment),
                    )
                else:
                    payment = await self._repo.update_status(
                        session=session,
                        payment=payment,
                        new_status=PaymentStatus.PROCESSING,
                    )
            else:
                payment = await self._transition_status(
                    session=session, payment=payment, new_status=PaymentStatus.FAILED
                )
                await self._publish_event(
                    "failed",
                    self._payload_builder.build_failed(
                        payment, f"Gateway returned status: {result['status']}"
                    ),
                )
        except Exception as exc:
            logger.exception("Payment creation failed for order %s", order_id)
            with contextlib.suppress(Exception):
                payment = await self._transition_status(
                    session=session, payment=payment, new_status=PaymentStatus.FAILED
                )
            await self._publish_event(
                "failed",
                self._payload_builder.build_failed(payment, str(exc)),
            )

        return payment

    async def _transition_status(
        self, *, session: AsyncSession, payment: Payment, new_status: PaymentStatus
    ) -> Payment:
        """Validate and apply a payment status transition.

        Raises:
            ConflictError: If the transition isn't allowed from the payment's
                current status.
        """
        current_status = PaymentStatus(payment.status)
        try:
            PAYMENT_STATE_MACHINE.assert_transition(current_status, new_status)
        except InvalidTransitionError as exc:
            msg = f"Cannot transition payment from {payment.status} to {new_status}"
            raise ConflictError(msg) from exc
        return await self._repo.update_status(
            session=session, payment=payment, new_status=new_status
        )

    async def get_payment(
        self,
        *,
        session: AsyncSession,
        payment_uuid: uuid.UUID,
        caller_id: uuid.UUID,
        caller_is_privileged: bool = False,
    ) -> Payment | None:
        """Fetch a payment by id — the payment's own buyer, or an admin.

        Returns None (not a distinct "forbidden" outcome) on an ownership
        mismatch, same as order-service's get_order() — the router turns
        that into 404, so a payment ID belonging to someone else isn't
        distinguishable from one that doesn't exist at all.
        """
        payment = await self._repo.get_by_uuid(session=session, uuid_value=payment_uuid)
        if payment is None:
            return None
        if not caller_is_privileged and payment.user_id != caller_id:
            return None
        return payment

    async def get_payment_by_order(
        self,
        *,
        session: AsyncSession,
        order_id: uuid.UUID,
        caller_id: uuid.UUID,
        caller_is_privileged: bool = False,
    ) -> Payment | None:
        """Fetch the payment for an order — same ownership rule as get_payment().

        A `None` return also covers the ordinary case of "order exists,
        payment hasn't been created yet" — not just ownership mismatches or
        a nonexistent order. The router doesn't need to (and can't cheaply)
        tell those apart from here.
        """
        payment = await self._repo.get_by_order_id(session=session, order_id=order_id)
        if payment is None:
            return None
        if not caller_is_privileged and payment.user_id != caller_id:
            return None
        return payment

    async def refund(
        self,
        *,
        session: AsyncSession,
        payment_uuid: uuid.UUID,
        amount: int | None = None,
    ) -> Payment:
        """Refund a successful payment."""
        payment = await self._repo.get_by_uuid(session=session, uuid_value=payment_uuid)
        if payment is None:
            msg = f"Payment not found: {payment_uuid}"
            raise NotFoundError(msg)

        if payment.status != PaymentStatus.SUCCEEDED:
            msg = f"Cannot refund payment with status {payment.status}"
            raise ConflictError(msg)

        if payment.gateway_payment_id is None:
            # Unreachable in practice: create_payment() always sets this
            # before a payment can reach SUCCEEDED. Guarded explicitly so a
            # future path that skips that assignment fails loudly here
            # instead of asking the gateway to refund "None".
            msg = f"Payment {payment_uuid} has no gateway_payment_id to refund"
            raise ConflictError(msg)

        gateway: BasePaymentGateway = self._registry.get_gateway(
            PaymentMethod(payment.payment_method)
        )

        refund_amount = amount or payment.amount

        result = await gateway.refund(payment.gateway_payment_id, refund_amount)

        transaction = Transaction(
            id=uuid7(),
            payment_id=payment.id,
            transaction_type=TransactionType.REFUND,
            amount=refund_amount,
            gateway_transaction_id=result.get("gateway_transaction_id"),
            metadata=result.get("raw_response"),
        )
        await self._repo.add_transaction(session=session, transaction=transaction)

        new_status = (
            PaymentStatus.REFUNDED
            if refund_amount >= payment.amount
            else PaymentStatus.PARTIALLY_REFUNDED
        )
        await self._transition_status(
            session=session, payment=payment, new_status=new_status
        )

        await self._publish_event(
            "refunded",
            self._payload_builder.build_refunded(payment, transaction),
        )

        return payment

    async def handle_stripe_webhook(
        self, *, session: AsyncSession, payload: str, signature: str
    ) -> None:
        """Process a Stripe webhook event."""
        gateway = self._registry.get_gateway(PaymentMethod.STRIPE)
        event = await gateway.verify_webhook(payload, signature)

        event_type = event.get("type", "")
        event_data = event.get("data", {}).get("object", {})

        if event_type == "payment_intent.succeeded":
            pi_id = event_data.get("id")
            if pi_id:
                payment = await self._repo.get_by_gateway_payment_id(
                    session=session, gateway_payment_id=pi_id
                )
                if payment and payment.status != PaymentStatus.SUCCEEDED:
                    await self._transition_status(
                        session=session,
                        payment=payment,
                        new_status=PaymentStatus.SUCCEEDED,
                    )
                    await self._publish_event(
                        "succeeded",
                        self._payload_builder.build_succeeded(payment),
                    )

        elif event_type == "payment_intent.payment_failed":
            pi_id = event_data.get("id")
            if pi_id:
                payment = await self._repo.get_by_gateway_payment_id(
                    session=session, gateway_payment_id=pi_id
                )
                if payment and payment.status != PaymentStatus.FAILED:
                    reason = event_data.get("last_payment_error", {}).get(
                        "message", "Payment failed"
                    )
                    await self._transition_status(
                        session=session,
                        payment=payment,
                        new_status=PaymentStatus.FAILED,
                    )
                    await self._publish_event(
                        "failed",
                        self._payload_builder.build_failed(payment, reason),
                    )

    async def handle_yookassa_webhook(
        self, *, session: AsyncSession, payload: str | bytes
    ) -> None:
        """Process a YooKassa webhook event."""
        gateway = self._registry.get_gateway(PaymentMethod.YOOKASSA)
        event = await gateway.verify_webhook(payload)

        event_type = event.get("event", "")
        event_object = event.get("object", {})

        if event_type == "payment.succeeded":
            payment_id = event_object.get("id")
            if payment_id:
                payment = await self._repo.get_by_gateway_payment_id(
                    session=session, gateway_payment_id=payment_id
                )
                if payment and payment.status != PaymentStatus.SUCCEEDED:
                    await self._transition_status(
                        session=session,
                        payment=payment,
                        new_status=PaymentStatus.SUCCEEDED,
                    )
                    await self._publish_event(
                        "succeeded",
                        self._payload_builder.build_succeeded(payment),
                    )

        elif event_type == "payment.canceled":
            payment_id = event_object.get("id")
            if payment_id:
                payment = await self._repo.get_by_gateway_payment_id(
                    session=session, gateway_payment_id=payment_id
                )
                if payment and payment.status != PaymentStatus.CANCELLED:
                    reason = event_object.get("cancellation_details", {}).get(
                        "reason", "Payment cancelled"
                    )
                    await self._transition_status(
                        session=session,
                        payment=payment,
                        new_status=PaymentStatus.CANCELLED,
                    )
                    await self._publish_event(
                        "failed",
                        self._payload_builder.build_failed(payment, reason),
                    )

    async def _publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Publish an event to RabbitMQ."""
        try:
            if event_type == "succeeded":
                await publish_payment_succeeded(payload)
            elif event_type == "failed":
                await publish_payment_failed(payload)
            elif event_type == "refunded":
                await publish_payment_refunded(payload)
        except Exception:
            logger.exception("Failed to publish event %s", event_type)
