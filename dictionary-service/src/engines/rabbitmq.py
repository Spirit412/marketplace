import json
import logging
from functools import lru_cache
from typing import Any

from src.config.settings import settings

logger = logging.getLogger(__name__)

try:
    import aio_pika

    _AIO_PIKA_AVAILABLE = True
except ImportError:
    _AIO_PIKA_AVAILABLE = False


class DictionaryPublisher:
    EXCHANGE_NAME = "marketplace.dictionary"
    ROUTING_KEY = "dictionary.updated"

    def __init__(self) -> None:
        self._settings = settings
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        if not _AIO_PIKA_AVAILABLE:
            logger.warning("aio_pika not installed; RabbitMQ publishing disabled")
            return
        self._connection = await aio_pika.connect_robust(
            self._settings.rabbitmq.url,
        )
        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(
            self.EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    async def disconnect(self) -> None:
        if self._connection and _AIO_PIKA_AVAILABLE:
            await self._connection.close()

    async def publish_dictionary_updated(self, payload: dict[str, Any]) -> None:
        if not _AIO_PIKA_AVAILABLE or self._exchange is None:
            logger.debug("RabbitMQ not available; skipping publish: %s", payload)
            return
        message = aio_pika.Message(
            body=json.dumps(payload, default=str).encode(),
            content_type="application/json",
        )
        await self._exchange.publish(
            message,
            routing_key=self.ROUTING_KEY,
        )


@lru_cache
def get_publisher() -> DictionaryPublisher:
    return DictionaryPublisher()
