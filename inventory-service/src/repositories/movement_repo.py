import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted
from src.models.models import StockItem, StockMovement


class MovementRepo:
    async def create(
        self, session: AsyncSession, movement: StockMovement
    ) -> StockMovement:
        session.add(movement)
        await session.flush()
        return movement

    async def list_by_stock_item(
        self,
        session: AsyncSession,
        stock_item_id: uuid.UUID,
        movement_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[StockMovement]:
        stmt = select(StockMovement).where(StockMovement.stock_item_id == stock_item_id)
        if movement_type:
            stmt = stmt.where(StockMovement.movement_type == movement_type)
        if date_from:
            stmt = stmt.where(StockMovement.created_at >= date_from)
        if date_to:
            stmt = stmt.where(StockMovement.created_at <= date_to)
        stmt = (
            stmt.order_by(StockMovement.created_at.desc()).offset(offset).limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_warehouse(
        self,
        session: AsyncSession,
        warehouse_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[StockMovement]:

        stmt = exclude_deleted(
            select(StockMovement)
            .join(StockItem, StockMovement.stock_item_id == StockItem.id)
            .where(StockItem.warehouse_id == warehouse_id)
            .order_by(StockMovement.created_at.desc())
            .offset(offset)
            .limit(limit),
            StockItem,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
