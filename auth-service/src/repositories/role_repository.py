from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, func, or_, select
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

    async def get_with_groups(
        self, session: AsyncSession, role_id: UUID
    ) -> Role | None:
        stmt = select(Role).where(Role.id == role_id).options(selectinload(Role.groups))
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
        stmt = select(func.count(Role.id))
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
        self, session: AsyncSession, role_id: UUID, group_ids: set[UUID]
    ) -> None:
        existing = await self._get_assigned_groups(session, role_id)
        to_add = group_ids - existing
        to_remove = existing - group_ids

        if to_remove:
            stmt = delete(RoleGroupAssociation).where(
                RoleGroupAssociation.role_id == role_id,
                RoleGroupAssociation.group_id.in_(to_remove),
            )
            await session.execute(stmt)

        for group_id in to_add:
            session.add(RoleGroupAssociation(role_id=role_id, group_id=group_id))

        await session.flush()

    async def _get_assigned_groups(
        self, session: AsyncSession, role_id: UUID
    ) -> set[UUID]:
        stmt = select(RoleGroupAssociation.group_id).where(
            RoleGroupAssociation.role_id == role_id
        )
        result = await session.execute(stmt)
        return set(result.scalars().all())
