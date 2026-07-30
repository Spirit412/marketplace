from functools import lru_cache

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
