import json
import logging
from functools import lru_cache

from src.config.settings import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_broker():
    """Return a simple RabbitMQ publisher (lazy, no aio_pika if unavailable)."""
    return


async def _publish_event(exchange: str, routing_key: str, payload: dict) -> None:
    """Publish event to RabbitMQ; if unavailable, log and ignore gracefully."""
    try:
        import aio_pika

        connection = await aio_pika.connect_robust(settings.rabbitmq.url)
        async with connection:
            channel = await connection.channel()
            exchange_obj = await channel.declare_exchange(
                exchange, aio_pika.ExchangeType.TOPIC, durable=True
            )
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                content_type="application/json",
            )
            await exchange_obj.publish(message, routing_key=routing_key)
    except ImportError:
        logger.debug(
            "aio_pika not installed; skipping publish to %s/%s",
            exchange,
            routing_key,
        )
    except Exception:
        logger.exception("Failed to publish event %s/%s", exchange, routing_key)


async def publish_payment_succeeded(payload: dict) -> None:
    """Publish payment.succeeded event."""
    await _publish_event("marketplace.payment", "payment.succeeded", payload)


async def publish_payment_failed(payload: dict) -> None:
    """Publish payment.failed event."""
    await _publish_event("marketplace.payment", "payment.failed", payload)


async def publish_payment_refunded(payload: dict) -> None:
    """Publish payment.refunded event."""
    await _publish_event("marketplace.payment", "payment.refunded", payload)
