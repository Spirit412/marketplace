import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted
from src.models.models import Warehouse


class WarehouseRepo:
    """Repository for Warehouse; soft-deleted rows are hidden unless asked for."""

    async def create(self, session: AsyncSession, warehouse: Warehouse) -> Warehouse:
        session.add(warehouse)
        await session.flush()
        return warehouse

    async def get_by_id(
        self, session: AsyncSession, warehouse_id: uuid.UUID
    ) -> Warehouse | None:
        stmt = exclude_deleted(
            select(Warehouse).where(
                Warehouse.id == warehouse_id, Warehouse.is_active.is_(True)
            ),
            Warehouse,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_seller(
        self,
        session: AsyncSession,
        seller_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Warehouse], int]:
        stmt = exclude_deleted(
            select(Warehouse)
            .where(Warehouse.seller_id == seller_id, Warehouse.is_active.is_(True))
            .order_by(Warehouse.name)
            .offset(offset)
            .limit(limit),
            Warehouse,
        )
        result = await session.execute(stmt)
        warehouses = list(result.scalars().all())
        total = len(warehouses)
        return warehouses, total

    async def update(self, session: AsyncSession, warehouse: Warehouse) -> Warehouse:
        await session.merge(warehouse)
        await session.flush()
        return warehouse

    async def deactivate(
        self, session: AsyncSession, warehouse_id: uuid.UUID
    ) -> Warehouse | None:
        stmt = (
            update(Warehouse)
            .where(Warehouse.id == warehouse_id)
            .values(is_active=False, updated_at=datetime.now(UTC))
            .returning(Warehouse)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name_and_seller(
        self, session: AsyncSession, name: str, seller_id: uuid.UUID
    ) -> Warehouse | None:
        stmt = select(Warehouse).where(
            Warehouse.name == name,
            Warehouse.seller_id == seller_id,
            Warehouse.is_active.is_(True),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
