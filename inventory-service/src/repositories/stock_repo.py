import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted
from src.models.models import StockItem


class StockRepo:
    """Repository for StockItem; soft-deleted rows are hidden unless asked for."""

    async def get_by_product_and_warehouse(
        self, session: AsyncSession, product_id: uuid.UUID, warehouse_id: uuid.UUID
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
        self, session: AsyncSession, stock_item_id: uuid.UUID
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

    async def get_or_create(
        self, session: AsyncSession, product_id: uuid.UUID, warehouse_id: uuid.UUID
    ) -> StockItem:
        item = await self.get_by_product_and_warehouse(session, product_id, warehouse_id)
        if item is None:
            item = StockItem(product_id=product_id, warehouse_id=warehouse_id)
            session.add(item)
            await session.flush()
        return item

    async def update_quantity(
        self,
        session: AsyncSession,
        stock_item_id: uuid.UUID,
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
        self, session: AsyncSession, product_id: uuid.UUID, warehouse_id: uuid.UUID
    ) -> int:
        item = await self.get_by_product_and_warehouse(session, product_id, warehouse_id)
        if item is None:
            return 0
        return item.quantity - item.reserved

    async def list_by_warehouse(
        self,
        session: AsyncSession,
        warehouse_id: uuid.UUID,
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

    async def list_by_product(
        self, session: AsyncSession, product_id: uuid.UUID
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
