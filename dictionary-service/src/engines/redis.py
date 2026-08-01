import json
from functools import lru_cache
from typing import Any

import redis.asyncio as redis_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.enums.dictionary_type import DictionaryType
from src.models.dictionary import DictionaryEntry


@lru_cache
def get_redis_client() -> redis_asyncio.Redis:
    return redis_asyncio.from_url(
        settings.redis.url,
        decode_responses=True,
    )


async def check_redis() -> None:
    client = get_redis_client()
    await client.ping()


class RedisDictCache:
    def __init__(self, redis_client: redis_asyncio.Redis | None = None) -> None:
        self._settings = settings
        self._redis = redis_client or get_redis_client()

    async def get(
        self, type_: str, code: str | None = None
    ) -> list[dict[str, Any]] | dict[str, Any] | None:
        if code is not None:
            key = f"dict:{type_}:{code}"
            data = await self._redis.get(key)
            result: dict[str, Any] | None = json.loads(data) if data else None
            return result
        keys = await self._redis.keys(f"dict:{type_}:*")
        items: list[dict[str, Any]] = []
        for redis_key in keys:
            data = await self._redis.get(redis_key)
            if data:
                items.append(json.loads(data))
        return items

    async def set(
        self, type_: str, data: list[dict[str, Any]], ttl: int | None = None
    ) -> None:
        if ttl is None:
            ttl = self._settings.CACHE_TTL_SECONDS

        pipeline = self._redis.pipeline()
        for item in data:
            code = item.get("code", "")
            key = f"dict:{type_}:{code}"
            pipeline.set(key, json.dumps(item, default=str), ex=ttl)
        await pipeline.execute()

    async def invalidate(self, type_: str) -> None:
        keys = await self._redis.keys(f"dict:{type_}:*")
        if keys:
            await self._redis.delete(*keys)

    async def warm_cache(self, async_session: AsyncSession) -> None:

        for dict_type in DictionaryType:
            stmt = select(DictionaryEntry).where(DictionaryEntry.type == dict_type)
            result = await async_session.execute(stmt)
            entries = list(result.scalars().all())
            if entries:
                data = [
                    {
                        "id": str(e.id),
                        "type": e.type,
                        "code": e.code,
                        "data": e.data,
                        "created_at": e.created_at.isoformat(),
                        "updated_at": e.updated_at.isoformat(),
                    }
                    for e in entries
                ]
                await self.set(dict_type.value, data)
