from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repository import BaseRepository
from src.models.role import Role
from src.models.role_group_association import RoleGroupAssociation


class RoleRepository(BaseRepository[Role]):
    def __init__(self) -> None:
        super().__init__(Role)

    async def get_by_name(self, session: AsyncSession, name: str) -> Role | None:
        return await self.get_by(session, name=name)

    async def get_with_groups(self, session: AsyncSession, uuid: UUID) -> Role | None:
        stmt = (
            select(Role)
            .where(Role.uuid == uuid)
            .options(selectinload(Role.groups))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def search(
        self,
        session: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        search_value: str | None = None,
    ) -> tuple[Sequence[Role], int, int]:
        stmt = select(Role)

        if search_value:
            stmt = stmt.where(
                or_(
                    Role.name.ilike(f"%{search_value}%"),
                    Role.description.ilike(f"%{search_value}%"),
                )
            )

        return await self._paginate_stmt(
            session=session,
            stmt=stmt,
            page=page,
            page_size=page_size,
        )

    async def search_count_only(
        self, session: AsyncSession, search_value: str | None = None
    ) -> int:
        stmt = select(func.count(Role.uuid))
        if search_value:
            stmt = stmt.where(
                or_(
                    Role.name.ilike(f"%{search_value}%"),
                    Role.description.ilike(f"%{search_value}%"),
                )
            )
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    async def assign_groups(
        self, session: AsyncSession, role_uuid: UUID, group_uuids: set[UUID]
    ) -> None:
        existing = await self._get_assigned_groups(session, role_uuid)
        to_add = group_uuids - existing
        to_remove = existing - group_uuids

        if to_remove:
            from sqlalchemy import delete

            stmt = delete(RoleGroupAssociation).where(
                RoleGroupAssociation.role_uuid == role_uuid,
                RoleGroupAssociation.group_uuid.in_(to_remove),
            )
            await session.execute(stmt)

        for group_uuid in to_add:
            session.add(
                RoleGroupAssociation(role_uuid=role_uuid, group_uuid=group_uuid)
            )

        await session.flush()

    async def _get_assigned_groups(
        self, session: AsyncSession, role_uuid: UUID
    ) -> set[UUID]:
        stmt = select(RoleGroupAssociation.group_uuid).where(
            RoleGroupAssociation.role_uuid == role_uuid
        )
        result = await session.execute(stmt)
        return {row for row in result.scalars().all()}
