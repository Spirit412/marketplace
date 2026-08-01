import json
import logging
from functools import lru_cache
from typing import Any

import aio_pika

from src.config.settings import settings

logger = logging.getLogger(__name__)


@lru_cache
def get_broker() -> None:
    """Return a simple RabbitMQ publisher (lazy, no aio_pika if unavailable)."""
    return


async def _publish_event(
    exchange: str, routing_key: str, payload: dict[str, Any]
) -> None:
    """Publish event to RabbitMQ; if unavailable, log and ignore gracefully."""
    try:
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
    except Exception:
        logger.exception("Failed to publish event %s/%s", exchange, routing_key)


async def publish_payment_succeeded(payload: dict[str, Any]) -> None:
    """Publish payment.succeeded event."""
    await _publish_event("marketplace.events", "payment.succeeded", payload)


async def publish_payment_failed(payload: dict[str, Any]) -> None:
    """Publish payment.failed event."""
    await _publish_event("marketplace.events", "payment.failed", payload)


async def publish_payment_refunded(payload: dict[str, Any]) -> None:
    """Publish payment.refunded event."""
    await _publish_event("marketplace.events", "payment.refunded", payload)
