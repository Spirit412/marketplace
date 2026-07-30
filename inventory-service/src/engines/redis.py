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


async def acquire_stock_lock(
    redis_client: redis_asyncio.Redis,
    product_id: str,
    warehouse_id: str,
    ttl: int | None = None,
) -> bool:
    """Acquire a distributed lock for stock operations using SETNX."""
    if ttl is None:
        ttl = settings.STOCK_LOCK_TTL
    lock_key = f"lock:stock:{product_id}:{warehouse_id}"
    token = "1"
    acquired = await redis_client.set(lock_key, token, nx=True, ex=ttl)
    return bool(acquired)


async def release_stock_lock(
    redis_client: redis_asyncio.Redis,
    product_id: str,
    warehouse_id: str,
) -> None:
    """Release a stock lock."""
    lock_key = f"lock:stock:{product_id}:{warehouse_id}"
    await redis_client.delete(lock_key)
