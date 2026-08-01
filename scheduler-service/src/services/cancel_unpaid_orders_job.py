import logging

from src.config.settings import settings
from src.engines.rabbitmq import publish_event
from src.facades import OrderClient

logger = logging.getLogger(__name__)


async def cancel_unpaid_orders_job() -> None:
    """Find and cancel orders stuck in pending_payment for too long."""
    client = OrderClient(settings.ORDER_SERVICE_URL, settings.SYSTEM_TOKEN)

    pending_orders = await client.get_pending_orders(
        older_than_minutes=settings.UNPAID_ORDER_TIMEOUT_MINUTES
    )

    if not pending_orders:
        logger.info("No unpaid orders to cancel")
        return

    logger.info("Found %d unpaid orders to cancel", len(pending_orders))

    for order in pending_orders:
        order_id = order.get("id", "")
        user_id = order.get("user_id", "")

        success = await client.cancel_order(order_id)
        if success:
            await publish_event(
                "order.cancelled",
                {
                    "order_id": order_id,
                    "user_id": user_id,
                    "reason": "payment_timeout",
                },
            )
            logger.info("Cancelled order %s", order_id)
        else:
            logger.warning("Failed to cancel order %s", order_id)
