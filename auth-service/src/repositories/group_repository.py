from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repository import BaseRepository
from src.models.group import Group
from src.models.permission import Permission
from src.models.permission_group_association import PermissionGroupAssociation


class GroupRepository(BaseRepository[Group]):
    def __init__(self) -> None:
        super().__init__(Group)

    async def get_with_permissions(
        self, session: AsyncSession, uuid: UUID
    ) -> Group | None:
        stmt = (
            select(Group)
            .where(Group.uuid == uuid)
            .options(selectinload(Group.permissions))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_roles(
        self, session: AsyncSession, uuid: UUID
    ) -> Group | None:
        stmt = (
            select(Group)
            .where(Group.uuid == uuid)
            .options(selectinload(Group.roles))
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
        stmt = (
            select(Group)
            .options(selectinload(Group.permissions))
        )

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

    async def check_by_uuids(
        self, session: AsyncSession, uuids: set[UUID]
    ) -> list[Group]:
        stmt = select(Group).where(Group.uuid.in_(uuids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def assign_permissions(
        self, session: AsyncSession, group_uuid: UUID, permission_uuids: set[UUID]
    ) -> None:
        existing = await self._get_assigned_permissions(session, group_uuid)
        to_add = permission_uuids - existing
        to_remove = existing - permission_uuids

        if to_remove:
            from sqlalchemy import delete

            stmt = delete(PermissionGroupAssociation).where(
                PermissionGroupAssociation.group_uuid == group_uuid,
                PermissionGroupAssociation.permission_uuid.in_(to_remove),
            )
            await session.execute(stmt)

        for perm_uuid in to_add:
            session.add(
                PermissionGroupAssociation(
                    group_uuid=group_uuid, permission_uuid=perm_uuid
                )
            )

        await session.flush()

    async def _get_assigned_permissions(
        self, session: AsyncSession, group_uuid: UUID
    ) -> set[UUID]:
        stmt = select(PermissionGroupAssociation.permission_uuid).where(
            PermissionGroupAssociation.group_uuid == group_uuid
        )
        result = await session.execute(stmt)
        return {row for row in result.scalars().all()}

    async def resolve_permissions_for_role(
        self, session: AsyncSession, role_uuid: UUID
    ) -> list[Permission]:
        """Get all permissions for a role through its groups."""
        from src.models.role import Role
        from src.models.role_group_association import RoleGroupAssociation

        stmt = (
            select(Permission)
            .join(
                PermissionGroupAssociation,
                PermissionGroupAssociation.permission_uuid == Permission.uuid,
            )
            .join(
                Group,
                Group.uuid == PermissionGroupAssociation.group_uuid,
            )
            .join(
                RoleGroupAssociation,
                RoleGroupAssociation.group_uuid == Group.uuid,
            )
            .where(RoleGroupAssociation.role_uuid == role_uuid)
            .distinct()
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
