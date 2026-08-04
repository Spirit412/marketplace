"""Consumes payment.succeeded/payment.failed for order-service.

Declared as a RabbitRouter (not directly on the module-level broker) so
event-group registration stays separate from broker/app wiring, and a new
event group (e.g. inventory.* later) can be added as its own router module
via broker.include_router() instead of growing one flat file.
"""

import logging
from typing import Any
from uuid import UUID

from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue, RabbitRouter

from src.config.settings import settings
from src.core.database import _get_session_factory
from src.engines.redis import get_redis_client
from src.facades import InventoryClient
from src.facades.catalog import CatalogClient
from src.repositories.order_repo import OrderRepo
from src.services.cart_service import CartService
from src.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = RabbitRouter()

# The bare-string form of @broker.subscriber("routing.key") binds to the
# default (nameless) exchange under that name — it does NOT reach a named
# topic exchange. payment-service publishes to the shared "marketplace.events"
# topic exchange (see payment-service/src/engines/rabbitmq.py), so the
# consumer needs an explicit queue+exchange pair to actually receive anything.
_EVENTS_EXCHANGE = RabbitExchange(
    "marketplace.events", type=ExchangeType.TOPIC, durable=True
)


def _build_order_service() -> OrderService:
    # Mirrors depends.py's registrations, minus the DI container — a worker
    # process resolves its own dependencies rather than going through FastAPI.
    return OrderService(
        order_repo=OrderRepo(),
        cart_service=CartService(get_redis_client()),
        inventory_client=InventoryClient(
            settings.INVENTORY_SERVICE_URL, settings.SYSTEM_TOKEN
        ),
        catalog_client=CatalogClient(
            settings.CATALOG_SERVICE_URL, settings.SYSTEM_TOKEN
        ),
        redis_client=get_redis_client(),
    )


@router.subscriber(
    RabbitQueue(
        "order-service.payment.succeeded", routing_key="payment.succeeded", durable=True
    ),
    _EVENTS_EXCHANGE,
)
async def handle_payment_succeeded(payload: dict[str, Any]) -> None:
    order_id = payload.get("order_id")
    if not order_id:
        logger.warning("payment.succeeded event missing order_id: %s", payload)
        return

    session_factory = _get_session_factory()
    async with session_factory() as session:
        service = _build_order_service()
        try:
            order = await service.confirm_payment(
                session=session, order_id=UUID(order_id)
            )
            await session.commit()
        except Exception:
            logger.exception(
                "Failed to confirm order %s after payment.succeeded", order_id
            )
            return

        if order is None:
            logger.info(
                "payment.succeeded for order %s: no-op (unknown order, or "
                "already past pending)",
                order_id,
            )
        else:
            logger.info("Order %s confirmed by payment.succeeded", order_id)


@router.subscriber(
    RabbitQueue(
        "order-service.payment.failed", routing_key="payment.failed", durable=True
    ),
    _EVENTS_EXCHANGE,
)
async def handle_payment_failed(payload: dict[str, Any]) -> None:
    # Deliberately not cancelling the order here — a failed attempt isn't a
    # final outcome (the buyer may retry with another payment_method). The
    # scheduler's cancel_unpaid_orders job is the backstop for orders that
    # never get a successful payment within the timeout. This handler exists
    # so the failure is at least visible in order-service's own logs.
    logger.info(
        "payment.failed for order %s: %s",
        payload.get("order_id"),
        payload.get("reason", ""),
    )
