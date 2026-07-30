import asyncio
import logging

from faststream.rabbit import RabbitBroker, RabbitRouter

from src.config.settings import settings

logger = logging.getLogger(__name__)
_lock = asyncio.Lock()
_broker: RabbitBroker | None = None


async def get_broker() -> RabbitBroker:
    global _broker
    if _broker is not None:
        return _broker

    async with _lock:
        if _broker is not None:
            return _broker

        _broker = RabbitBroker(settings.rabbitmq.url)
        await _broker.connect()
        logger.info("RabbitMQ broker connected")

    return _broker


async def check_rabbitmq() -> None:
    broker = await get_broker()
    if broker is None or not broker._connection:
        raise RuntimeError("RabbitMQ not connected")


def create_subscriber_router() -> RabbitRouter:
    """Factory for a fresh FastStream RabbitRouter to attach @router.subscriber(...) handlers to."""
    return RabbitRouter()
