from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repository import BaseRepository
from src.models.role import Role
from src.models.user_access import UserAccess


class UserAccessRepository(BaseRepository[UserAccess]):
    def __init__(self) -> None:
        super().__init__(UserAccess)

    async def get_by_user(
        self, session: AsyncSession, user_uuid: UUID
    ) -> UserAccess | None:
        stmt = (
            select(UserAccess)
            .where(UserAccess.user_uuid == user_uuid)
            .options(
                selectinload(UserAccess.role).selectinload(Role.groups),
                selectinload(UserAccess.permissions),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        session: AsyncSession,
        *,
        user_uuid: UUID,
        role_uuid: UUID | None,
        additional_permissions: list[UUID] | None = None,
    ) -> UserAccess:
        existing = await self.get_by(session, user_uuid=user_uuid)
        if existing:
            existing.role_uuid = role_uuid
            if additional_permissions is not None:
                existing.additional_permissions = additional_permissions
            await session.flush()
            return existing

        user_access = UserAccess(
            user_uuid=user_uuid,
            role_uuid=role_uuid,
            additional_permissions=additional_permissions or [],
        )
        session.add(user_access)
        await session.flush()
        return user_access

    async def delete_for_user(
        self, session: AsyncSession, user_uuid: UUID
    ) -> None:
        stmt = delete(UserAccess).where(UserAccess.user_uuid == user_uuid)
        await session.execute(stmt)
        await session.flush()
