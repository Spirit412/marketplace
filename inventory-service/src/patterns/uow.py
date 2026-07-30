from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.engines.redis import get_redis_client
from src.repositories.movement_repo import MovementRepo
from src.repositories.stock_repo import StockRepo


class InventoryUnitOfWork:
    """Context manager for atomic inventory operations.

    Wraps a PostgreSQL session and Redis client, ensuring both are
    consistent: commit on success, rollback on exception, and cache
    invalidation.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._redis = get_redis_client()
        self.stock: StockRepo = StockRepo()
        self.movements: MovementRepo = MovementRepo()
        self._dirty_keys: set[str] = set()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_type is not None:
            await self._session.rollback()
            return False

        await self._session.commit()

        for key in self._dirty_keys:
            await self._redis.delete(key)

        return False

    def invalidate_stock_cache(
        self, product_id: str, warehouse_id: str
    ) -> None:
        """Mark a stock cache key for invalidation on commit."""
        self._dirty_keys.add(f"stock:{warehouse_id}:{product_id}")
