import json
from functools import lru_cache
from typing import Any

import redis.asyncio as redis_asyncio

from src.config.settings import settings


@lru_cache
def get_redis_client() -> redis_asyncio.Redis:
        return redis_asyncio.from_url(
        settings.redis.url,
        decode_responses=True,
    )


async def check_redis() -> None:
    client = get_redis_client()
    await client.ping()


class RedisCache:
    """Thin wrapper with JSON serialization helpers."""

    def __init__(self, client: redis_asyncio.Redis) -> None:
        self._client = client

    async def get_json(self, key: str) -> Any | None:
        data = await self._client.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def setex_json(self, key: str, ttl: int, value: Any) -> None:
        await self._client.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def ping(self) -> bool:
        return await self._client.ping()
