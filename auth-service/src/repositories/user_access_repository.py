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
        self, session: AsyncSession, user_id: UUID
    ) -> UserAccess | None:
        stmt = (
            select(UserAccess)
            .where(UserAccess.user_id == user_id)
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
        user_id: UUID,
        role_uuid: UUID | None,
        additional_permissions: list[UUID] | None = None,
    ) -> UserAccess:
        existing = await self.get_by(session, user_id=user_id)
        if existing:
            existing.role_uuid = role_uuid
            if additional_permissions is not None:
                existing.additional_permissions = additional_permissions
            await session.flush()
            # updated_at is server-side (onupdate=func.now()) — flush() alone
            # leaves it expired on the Python object; the next (synchronous)
            # attribute read, e.g. Pydantic serializing the response, would
            # need to lazy-load it and fail with MissingGreenlet outside an
            # await.
            await session.refresh(existing)
            return existing

        user_access = UserAccess(
            user_id=user_id,
            role_uuid=role_uuid,
            additional_permissions=additional_permissions or [],
        )
        session.add(user_access)
        await session.flush()
        await session.refresh(user_access)
        return user_access

    async def delete_for_user(self, session: AsyncSession, user_id: UUID) -> None:
        stmt = delete(UserAccess).where(UserAccess.user_id == user_id)
        await session.execute(stmt)
        await session.flush()
