import redis.asyncio as redis_asyncio

from src.config.settings import settings


class CartService:
    """Manages user shopping carts in Redis."""

    def __init__(self, redis_client: redis_asyncio.Redis) -> None:
        self._redis = redis_client

    @staticmethod
    def _build_key(user_uuid: str) -> str:
        return f"cart:{user_uuid}"

    async def get_cart(self, user_uuid: str) -> dict[str, int]:
        """Get all items in cart as {product_uuid: quantity}."""
        key = self._build_key(user_uuid)
        raw = await self._redis.hgetall(key)
        return {k: int(v) for k, v in raw.items()}

    async def add_item(
        self, user_uuid: str, product_uuid: str, quantity: int = 1
    ) -> dict[str, int]:
        """Add or increment a product in the cart."""
        key = self._build_key(user_uuid)
        await self._redis.hincrby(key, product_uuid, quantity)
        ttl = settings.CART_TTL_DAYS * 86400
        await self._redis.expire(key, ttl)
        return await self.get_cart(user_uuid)

    async def remove_item(
        self, user_uuid: str, product_uuid: str
    ) -> None:
        """Remove a product from the cart."""
        key = self._build_key(user_uuid)
        await self._redis.hdel(key, product_uuid)

    async def clear_cart(self, user_uuid: str) -> None:
        """Delete the entire cart."""
        key = self._build_key(user_uuid)
        await self._redis.delete(key)

    async def get_cart_count(self, user_uuid: str) -> int:
        """Return number of distinct items in cart."""
        key = self._build_key(user_uuid)
        return await self._redis.hlen(key)
