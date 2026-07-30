import json
from typing import Any

import aio_pika

from src.config.settings import settings


class RabbitMQEngine:
    def __init__(self) -> None:
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(
            settings.rabbitmq.url,
        )
        self._channel = await self._connection.channel()

    async def declare_exchange(self, name: str) -> aio_pika.abc.AbstractExchange:
        if self._channel is None:
            raise RuntimeError("RabbitMQ not connected")
        return await self._channel.declare_exchange(
            name,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        if self._channel is None:
            raise RuntimeError("RabbitMQ not connected")
        exchange = await self.declare_exchange(routing_key.split(".", maxsplit=1)[0])
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
        )
        await exchange.publish(message, routing_key=routing_key)

    async def close(self) -> None:
        if self._channel is not None:
            await self._channel.close()
        if self._connection is not None:
            await self._connection.close()
