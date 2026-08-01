import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from src.config.settings import settings
from src.core.database import _get_session_factory
from src.engines.rabbitmq import publish_event

logger = logging.getLogger(__name__)


async def cart_cleanup_job() -> None:
    """Remove carts not updated in CART_EXPIRY_DAYS days."""
    cutoff = datetime.now(UTC) - timedelta(days=settings.CART_EXPIRY_DAYS)

    factory = _get_session_factory()
    async with factory() as session:
        result = await session.execute(
            text("SELECT id, user_id FROM cart.carts WHERE updated_at < :cutoff"),
            {"cutoff": cutoff},
        )
        expired_carts = result.fetchall()

        if not expired_carts:
            logger.info("No expired carts to clean up")
            return

        logger.info("Cleaning up %d expired carts", len(expired_carts))

        for cart_id, user_id in expired_carts:
            await publish_event(
                "cart.expired",
                {
                    "cart_id": str(cart_id),
                    "user_id": str(user_id),
                    "reason": "expired",
                },
            )

        await session.execute(
            text("DELETE FROM cart.carts WHERE updated_at < :cutoff"),
            {"cutoff": cutoff},
        )
        await session.commit()

    logger.info("Cart cleanup completed: %d carts removed", len(expired_carts))
