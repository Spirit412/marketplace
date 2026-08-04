from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repository import BaseRepository
from src.models.group import Group
from src.models.permission import Permission
from src.models.permission_group_association import PermissionGroupAssociation
from src.models.role_group_association import RoleGroupAssociation


class GroupRepository(BaseRepository[Group]):
    def __init__(self) -> None:
        super().__init__(Group)

    async def get_with_permissions(
        self, session: AsyncSession, group_id: UUID
    ) -> Group | None:
        stmt = (
            select(Group)
            .where(Group.id == group_id)
            .options(selectinload(Group.permissions))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_roles(
        self, session: AsyncSession, group_id: UUID
    ) -> Group | None:
        stmt = (
            select(Group).where(Group.id == group_id).options(selectinload(Group.roles))
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
    ) -> tuple[Sequence[Group], int, int]:
        stmt = select(Group).options(selectinload(Group.permissions))

        if search_value:
            stmt = stmt.where(
                or_(
                    Group.name.ilike(f"%{search_value}%"),
                    Group.description.ilike(f"%{search_value}%"),
                )
            )

        return await self._paginate_stmt(
            session=session,
            stmt=stmt,
            page=page,
            page_size=page_size,
        )

    async def check_by_ids(self, session: AsyncSession, ids: set[UUID]) -> list[Group]:
        stmt = select(Group).where(Group.id.in_(ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def assign_permissions(
        self, session: AsyncSession, group_id: UUID, permission_ids: set[UUID]
    ) -> None:
        existing = await self._get_assigned_permissions(session, group_id)
        to_add = permission_ids - existing
        to_remove = existing - permission_ids

        if to_remove:
            stmt = delete(PermissionGroupAssociation).where(
                PermissionGroupAssociation.group_id == group_id,
                PermissionGroupAssociation.permission_id.in_(to_remove),
            )
            await session.execute(stmt)

        for perm_id in to_add:
            session.add(
                PermissionGroupAssociation(group_id=group_id, permission_id=perm_id)
            )

        await session.flush()

    async def _get_assigned_permissions(
        self, session: AsyncSession, group_id: UUID
    ) -> set[UUID]:
        stmt = select(PermissionGroupAssociation.permission_id).where(
            PermissionGroupAssociation.group_id == group_id
        )
        result = await session.execute(stmt)
        return set(result.scalars().all())

    async def resolve_permissions_for_role(
        self, session: AsyncSession, role_id: UUID
    ) -> list[Permission]:
        """Get all permissions for a role through its groups."""
        stmt = (
            select(Permission)
            .join(
                PermissionGroupAssociation,
                PermissionGroupAssociation.permission_id == Permission.id,
            )
            .join(
                Group,
                Group.id == PermissionGroupAssociation.group_id,
            )
            .join(
                RoleGroupAssociation,
                RoleGroupAssociation.group_id == Group.id,
            )
            .where(RoleGroupAssociation.role_id == role_id)
            .distinct()
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
