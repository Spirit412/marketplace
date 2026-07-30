import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import BaseRepository
from src.models.user import SessionLog


class SessionRepository(BaseRepository[SessionLog]):
    def __init__(self) -> None:
        super().__init__(SessionLog)

    async def get_by_jti(self, session: AsyncSession, jti: str) -> SessionLog | None:
        return await self.get_by(session, session_jti=jti)

    async def get_active_for_user(
        self, session: AsyncSession, user_uuid: uuid.UUID
    ) -> list[SessionLog]:
        from sqlalchemy import select

        stmt = (
            select(SessionLog)
            .where(SessionLog.user_uuid == user_uuid)
            .where(SessionLog.logout_at.is_(None))
            .order_by(SessionLog.login_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def close_session(self, session: AsyncSession, jti: str) -> None:
        from datetime import UTC, datetime

        stmt = (
            update(SessionLog)
            .where(SessionLog.session_jti == jti)
            .values(logout_at=datetime.now(UTC))
        )
        await session.execute(stmt)
        await session.flush()

    async def close_all_for_user(
        self, session: AsyncSession, user_uuid: uuid.UUID
    ) -> None:
        from datetime import UTC, datetime

        stmt = (
            update(SessionLog)
            .where(SessionLog.user_uuid == user_uuid)
            .where(SessionLog.logout_at.is_(None))
            .values(logout_at=datetime.now(UTC))
        )
        await session.execute(stmt)
        await session.flush()
