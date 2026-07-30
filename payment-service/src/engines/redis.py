from functools import lru_cache

import redis.asyncio as redis_asyncio

from src.config.settings import settings

IDEMPOTENCY_TTL = 86400


@lru_cache
def get_redis_client() -> redis_asyncio.Redis:
        return redis_asyncio.from_url(
        settings.redis.url,
        decode_responses=True,
    )


async def check_redis() -> None:
    client = get_redis_client()
    await client.ping()


async def check_idempotency(
    client: redis_asyncio.Redis, key: str
) -> bool:
    """Returns True if the key was set (first request), False if duplicate."""
    result = await client.setnx(f"idempotency:{key}", "1")
    if result:
        await client.expire(f"idempotency:{key}", IDEMPOTENCY_TTL)
        return True
    return False


async def delete_idempotency(
    client: redis_asyncio.Redis, key: str
) -> None:
    await client.delete(f"idempotency:{key}")
