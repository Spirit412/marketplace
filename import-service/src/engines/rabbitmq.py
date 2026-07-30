from typing import Any

import aio_pika
import orjson
from aio_pika.abc import AbstractChannel, AbstractRobustConnection

from src.config.settings import settings

EXCHANGE_NAME = "import.events"


class ImportPublisher:
    def __init__(self) -> None:
        self._connection: AbstractRobustConnection | None = None
        self._channel: AbstractChannel | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(settings.rabbitmq.url)
        self._channel = await self._connection.channel()
        await self._channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def disconnect(self) -> None:
        if self._channel is not None:
            await self._channel.close()
        if self._connection is not None:
            await self._connection.close()

    async def _publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        if self._channel is None:
            return
        exchange = await self._channel.get_exchange(EXCHANGE_NAME)
        message = aio_pika.Message(
            body=orjson.dumps(payload),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=routing_key)

    async def publish_import_validated(
        self, task_id: str, data: dict[str, Any]
    ) -> None:
        await self._publish(
            "import.validated",
            {"task_id": task_id, "data": data},
        )

    async def publish_import_completed(self, payload: dict[str, Any]) -> None:
        await self._publish("import.completed", payload)

    async def publish_import_failed(self, payload: dict[str, Any]) -> None:
        await self._publish("import.failed", payload)
