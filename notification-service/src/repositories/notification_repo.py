from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted
from src.models.notification import Notification


class NotificationRepository:
    """Repository for Notification; soft-deleted rows are hidden unless asked for."""

    async def create(
        self, session: AsyncSession, notification: Notification
    ) -> Notification:
        session.add(notification)
        await session.flush()
        return notification

    async def get_by_id(
        self, session: AsyncSession, notification_id: UUID
    ) -> Notification | None:
        stmt = exclude_deleted(
            select(Notification).where(Notification.id == notification_id),
            Notification,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_unread(
        self,
        session: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        stmt = exclude_deleted(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.status == "unread")
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset),
            Notification,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_history(
        self,
        session: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        stmt = exclude_deleted(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset),
            Notification,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def mark_read(
        self, session: AsyncSession, notification_id: UUID
    ) -> Notification | None:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(status="read", read_at=datetime.now(UTC))
            .returning(Notification)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self, session: AsyncSession, notification_id: UUID, status: str
    ) -> Notification | None:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(status=status)
            .returning(Notification)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
