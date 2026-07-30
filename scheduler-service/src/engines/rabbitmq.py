import asyncio
import json
import logging
from typing import Any

import aio_pika

from src.config.settings import settings

logger = logging.getLogger(__name__)

_connection: aio_pika.RobustConnection | None = None
_channel: aio_pika.abc.AbstractChannel | None = None
_lock = asyncio.Lock()


async def _get_channel() -> aio_pika.abc.AbstractChannel:
    global _connection, _channel

    if _channel is not None and not _channel.is_closed:
        return _channel

    async with _lock:
        if _channel is not None and not _channel.is_closed:
            return _channel

        _connection = await aio_pika.connect_robust(settings.rabbitmq.url)
        _channel = await _connection.channel()
        logger.info("RabbitMQ publisher connected")

    return _channel


async def publish_event(event_type: str, payload: dict[str, Any]) -> None:
    """Publish an event to the marketplace.events exchange."""
    channel = await _get_channel()

    exchange = await channel.declare_exchange(
        "marketplace.events", aio_pika.ExchangeType.TOPIC, durable=True
    )

    routing_key = event_type

    message = aio_pika.Message(
        body=json.dumps(payload).encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )

    await exchange.publish(message, routing_key=routing_key)
    logger.info("Published event: %s", event_type)


async def check_rabbitmq() -> None:
    channel = await _get_channel()
    if channel.is_closed:
        raise RuntimeError("RabbitMQ channel closed")


async def close_rabbitmq() -> None:
    global _connection, _channel
    if _channel is not None and not _channel.is_closed:
        await _channel.close()
    if _connection is not None and not _connection.is_closed:
        await _connection.close()
    _connection = None
    _channel = None
