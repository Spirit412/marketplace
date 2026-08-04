from redis import asyncio as redis_asyncio

from src.config.settings import Settings


class RateLimitService:
    """Reads the login rate-limit counter set by `enforce_login_rate_limit`."""

    def __init__(self, redis_client: redis_asyncio.Redis, settings: Settings) -> None:
        self._redis = redis_client
        self._settings = settings

    async def get_status(self, ip_address: str) -> dict[str, object]:
        key = f"{self._settings.REDIS_KEY_PREFIX}:rate_limit:{ip_address}"
        current = await self._redis.get(key)
        return {
            "ip": ip_address,
            "current_count": int(current) if current else 0,
        }
