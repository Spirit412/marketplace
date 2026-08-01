import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth_middleware import _get_auth_state
from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.core.database import get_async_session
from src.depends import Inject
from src.exceptions import NotFoundError
from src.schemes.request.payment import CreatePaymentRequest, RefundRequest
from src.schemes.response.payment import PaymentResponse
from src.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/",
    status_code=201,
    summary="Create payment",
)
async def create_payment(
    body: CreatePaymentRequest,
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[PaymentService, Depends(Inject(PaymentService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> PaymentResponse:
    """Create a new payment for an order."""
    payment = await service.create_payment(
        session=session,
        order_id=body.order_id,
        user_id=body.user_id,
        amount=body.amount,
        currency=body.currency,
        payment_method=body.payment_method,
        idempotency_key=body.idempotency_key,
    )
    return PaymentResponse.model_validate(payment)


@router.get(
    "/by-order/{order_id}",
    summary="Get the payment for an order",
)
async def get_payment_by_order(
    order_id: uuid.UUID,
    request: Request,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[PaymentService, Depends(Inject(PaymentService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> PaymentResponse:
    """Get the payment for an order — the order's own buyer, or an admin.

    Must stay declared before GET /{payment_uuid} below — a static segment
    ("by-order") after a parameterised one would be swallowed as an
    (invalid) UUID path param instead of matching here; see
    order-service's GET /orders/pending for the same rule.

    404 both when the order has no payment yet (still `pending`) and when
    the caller doesn't own it — same ownership-hides-behind-404 rule as
    GET /{payment_uuid}. Built for api-service's GET /orders/{id}/full
    composition (see PLAN_api-service.md), also usable directly.
    """
    auth_state = _get_auth_state(request)
    payment = await service.get_payment_by_order(
        session=session,
        order_id=order_id,
        caller_id=uuid.UUID(token_payload.user_id),
        caller_is_privileged=auth_state.is_admin,
    )
    if payment is None:
        msg = f"No payment found for order {order_id}"
        raise NotFoundError(msg)
    return PaymentResponse.model_validate(payment)


@router.get(
    "/{payment_uuid}",
    summary="Get payment by ID",
)
async def get_payment(
    payment_uuid: uuid.UUID,
    request: Request,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[PaymentService, Depends(Inject(PaymentService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> PaymentResponse:
    """Get payment details by UUID — the payment's own buyer, or an admin."""
    auth_state = _get_auth_state(request)
    payment = await service.get_payment(
        session=session,
        payment_uuid=payment_uuid,
        caller_id=uuid.UUID(token_payload.user_id),
        caller_is_privileged=auth_state.is_admin,
    )
    if payment is None:
        msg = f"Payment {payment_uuid} not found"
        raise NotFoundError(msg)
    return PaymentResponse.model_validate(payment)


@router.post(
    "/{payment_uuid}/refund",
    summary="Refund payment",
)
async def refund_payment(
    payment_uuid: uuid.UUID,
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[PaymentService, Depends(Inject(PaymentService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    body: RefundRequest | None = None,
) -> PaymentResponse:
    """Refund a payment partially or in full.

    Unlike GET above, this has no resource-level ownership check yet — only
    the RBAC gate on PAYMENT:POST (sellers/admins). Confirming "is this
    caller the seller of *this* payment's order" needs a cross-service
    lookup into order-service that isn't wired up here; left as a known gap
    rather than bolted on as part of this change.
    """
    payment = await service.refund(
        session=session,
        payment_uuid=payment_uuid,
        amount=body.amount if body is not None else None,
    )
    return PaymentResponse.model_validate(payment)
