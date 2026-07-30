"""Order repository — inherits from BaseRepository."""


import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repository import BaseRepository
from src.models.order import Order, OrderItem, OrderStatusHistory


class OrderRepo(BaseRepository[Order]):
    def __init__(self) -> None:
        super().__init__(Order)

    async def get_by_uuid(
        self, session: AsyncSession, order_uuid: uuid.UUID
    ) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_uuid)
            .options(selectinload(Order.items))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        session: AsyncSession,
        user_uuid: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Order], int]:
        offset = (page - 1) * page_size
        count_stmt = (
            select(func.count()).select_from(Order).where(Order.user_uuid == user_uuid)
        )
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = (
            select(Order)
            .where(Order.user_uuid == user_uuid)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        orders = list((await session.execute(stmt)).scalars().unique().all())
        return orders, total

    async def update_status(
        self,
        session: AsyncSession,
        order: Order,
        new_status: str,
        *,
        changed_by: uuid.UUID | None = None,
        comment: str | None = None,
    ) -> Order:
        history_entry = OrderStatusHistory(
            order_id=order.id,
            from_status=order.status,
            to_status=new_status,
            changed_by=changed_by,
            comment=comment,
        )
        session.add(history_entry)
        order.status = new_status
        await session.flush()
        return order

    async def get_expired_orders(
        self, session: AsyncSession, expiration_minutes: int
    ) -> list[Order]:
        cutoff = datetime.now(UTC) - timedelta(minutes=expiration_minutes)
        stmt = (
            select(Order)
            .where(Order.status == "pending")
            .where(Order.created_at < cutoff)
            .options(selectinload(Order.items))
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_by_idempotency_key(
        self, session: AsyncSession, key: str
    ) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.idempotency_key == key)
            .options(selectinload(Order.items))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class OrderItemRepo(BaseRepository[OrderItem]):
    def __init__(self) -> None:
        super().__init__(OrderItem)
