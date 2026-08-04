from uuid import UUID

import redis.asyncio as redis_asyncio

from src.config.settings import settings
from src.schemes.response.cart import CartItemResponse, CartResponse


class CartService:
    """Manages user shopping carts in Redis."""

    def __init__(self, redis_client: redis_asyncio.Redis) -> None:
        self._redis = redis_client

    @staticmethod
    def _build_key(user_id: str) -> str:
        return f"cart:{user_id}"

    @staticmethod
    def _to_response(items: dict[str, int]) -> CartResponse:
        return CartResponse(
            items=[
                CartItemResponse(product_id=UUID(k), quantity=v)
                for k, v in items.items()
            ]
        )

    async def get_cart(self, user_id: str) -> dict[str, int]:
        """Get all items in cart as {product_id: quantity}."""
        key = self._build_key(user_id)
        raw = await self._redis.hgetall(key)
        # decode_responses=True on the client means these are always str at
        # runtime; the client's own typing leaves the key/value type as
        # `bytes | str` since it can't know that from the call site.
        return {
            (k.decode() if isinstance(k, bytes) else k): int(v) for k, v in raw.items()
        }

    async def get_cart_response(self, user_id: str) -> CartResponse:
        """Get current cart, shaped as the HTTP response schema."""
        return self._to_response(await self.get_cart(user_id))

    async def add_item(
        self, user_id: str, product_id: str, quantity: int = 1
    ) -> dict[str, int]:
        """Add or increment a product in the cart."""
        key = self._build_key(user_id)
        await self._redis.hincrby(key, product_id, quantity)
        ttl = settings.CART_TTL_DAYS * 86400
        await self._redis.expire(key, ttl)
        return await self.get_cart(user_id)

    async def add_item_response(
        self, user_id: str, product_id: str, quantity: int = 1
    ) -> CartResponse:
        """Add or increment a product; returns the HTTP response schema."""
        return self._to_response(await self.add_item(user_id, product_id, quantity))

    async def remove_item(self, user_id: str, product_id: str) -> None:
        """Remove a product from the cart."""
        key = self._build_key(user_id)
        await self._redis.hdel(key, product_id)

    async def clear_cart(self, user_id: str) -> None:
        """Delete the entire cart."""
        key = self._build_key(user_id)
        await self._redis.delete(key)

    async def get_cart_count(self, user_id: str) -> int:
        """Return number of distinct items in cart."""
        key = self._build_key(user_id)
        return await self._redis.hlen(key)
