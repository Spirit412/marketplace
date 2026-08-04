from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repository import BaseRepository
from src.models.role import Role
from src.models.user import User
from src.models.user_access import UserAccess


class UserRepository(BaseRepository[User]):
    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        return await self.get_by(session, email=email)

    async def get_with_access(
        self, session: AsyncSession, user_id: UUID
    ) -> User | None:
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.user_accesses)
                .selectinload(UserAccess.role)
                .selectinload(Role.groups),
                selectinload(User.user_accesses).selectinload(UserAccess.permissions),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def block(
        self,
        session: AsyncSession,
        user_id: UUID,
        blocked_by: UUID,
        reason: str,
    ) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_blocked=True, blocked_by=blocked_by, block_reason=reason)
            .returning(User)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def unblock(self, session: AsyncSession, user_id: UUID) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_blocked=False, blocked_by=None, block_reason=None)
            .returning(User)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
