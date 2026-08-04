from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted
from src.models.models import StockItem


class StockRepo:
    """Repository for StockItem; soft-deleted rows are hidden unless asked for."""

    async def get_by_product_and_warehouse(
        self, session: AsyncSession, product_id: UUID, warehouse_id: UUID
    ) -> StockItem | None:
        stmt = exclude_deleted(
            select(StockItem).where(
                StockItem.product_id == product_id,
                StockItem.warehouse_id == warehouse_id,
            ),
            StockItem,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(
        self, session: AsyncSession, stock_item_id: UUID
    ) -> StockItem | None:
        stmt = exclude_deleted(
            select(StockItem).where(StockItem.id == stock_item_id), StockItem
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, stock_item: StockItem) -> StockItem:
        session.add(stock_item)
        await session.flush()
        return stock_item

    async def commit(self, session: AsyncSession) -> None:
        """Force the current transaction durable now, ahead of the request's own commit.

        reserve()/release() need this: they hold a Redis lock only for the
        duration of the request, but get_async_session()'s own commit only
        runs once the request unwinds all the way back up through the
        router — well after the lock is released. Without an early commit
        here, a second concurrent request can acquire the lock and read
        this row before the first request's UPDATE is durable, and both
        would over-reserve stock beyond what physically exists.
        """
        await session.commit()

    async def get_or_create(
        self, session: AsyncSession, product_id: UUID, warehouse_id: UUID
    ) -> StockItem:
        item = await self.get_by_product_and_warehouse(
            session, product_id, warehouse_id
        )
        if item is None:
            item = StockItem(product_id=product_id, warehouse_id=warehouse_id)
            session.add(item)
            await session.flush()
        return item

    async def update_quantity(
        self,
        session: AsyncSession,
        stock_item_id: UUID,
        quantity_delta: int = 0,
        reserved_delta: int = 0,
    ) -> StockItem | None:
        """Atomically update quantity and/or reserved with row lock."""
        stmt = (
            update(StockItem)
            .where(StockItem.id == stock_item_id)
            .values(
                quantity=StockItem.quantity + quantity_delta,
                reserved=StockItem.reserved + reserved_delta,
            )
            .returning(StockItem)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_available_quantity(
        self, session: AsyncSession, product_id: UUID, warehouse_id: UUID
    ) -> int:
        item = await self.get_by_product_and_warehouse(
            session, product_id, warehouse_id
        )
        if item is None:
            return 0
        return item.quantity - item.reserved

    async def list_by_warehouse(
        self,
        session: AsyncSession,
        warehouse_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[StockItem]:
        stmt = exclude_deleted(
            select(StockItem)
            .where(StockItem.warehouse_id == warehouse_id)
            .offset(offset)
            .limit(limit),
            StockItem,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_low_stock(
        self, session: AsyncSession, threshold: int, limit: int = 500
    ) -> list[StockItem]:
        """Stock items at or below threshold.

        Available quantity is (quantity - reserved). Threshold is
        caller-supplied rather than a stored per-item column —
        StockItem has no per-product minimum in this schema, so the alert
        job passes its own STOCK_DEPLETION_THRESHOLD setting.
        """
        available = StockItem.quantity - StockItem.reserved
        stmt = (
            exclude_deleted(select(StockItem).where(available <= threshold), StockItem)
            .order_by(available.asc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_product(
        self, session: AsyncSession, product_id: UUID
    ) -> list[StockItem]:
        """All stock items for a product across every warehouse.

        Used to pick a warehouse when the caller (e.g. order-service) only
        knows the product, not which specific warehouse to reserve from.
        Ordered by available quantity (quantity - reserved) descending so the
        best-stocked warehouse is tried first.
        """
        stmt = exclude_deleted(
            select(StockItem).where(StockItem.product_id == product_id), StockItem
        )
        result = await session.execute(stmt)
        items = list(result.scalars().all())
        items.sort(key=lambda item: item.available, reverse=True)
        return items
