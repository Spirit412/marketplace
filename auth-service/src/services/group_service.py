from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError
from src.models.group import Group
from src.repositories.group_repository import GroupRepository
from src.repositories.permission_repository import PermissionRepository
from src.schemes.rbac import (
    GroupCreateRequest,
    GroupListResponse,
    GroupResponse,
    GroupUpdateRequest,
    PaginationParams,
)


class GroupService:
    def __init__(
        self, repo: GroupRepository, permission_repo: PermissionRepository
    ) -> None:
        self._repo = repo
        self._permission_repo = permission_repo

    async def create(
        self, session: AsyncSession, body: GroupCreateRequest
    ) -> GroupResponse:
        if body.permission_uuids:
            existing = await self._permission_repo.check_by_uuids(
                session, set(body.permission_uuids)
            )
            found_uuids = {p.uuid for p in existing}
            missing = set(body.permission_uuids) - found_uuids
            if missing:
                raise NotFoundError(f"Permissions not found: {missing}")

        group = Group(name=body.name, description=body.description)
        result = await self._repo.create(session, group)

        if body.permission_uuids:
            await self._repo.assign_permissions(
                session, result.uuid, set(body.permission_uuids)
            )

        return GroupResponse(
            uuid=result.uuid,
            name=result.name,
            description=result.description,
            permission_uuids=body.permission_uuids,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    async def get_by(self, session: AsyncSession, uuid: UUID) -> GroupResponse:
        group = await self._repo.get_with_permissions(session, uuid)
        if not group:
            raise NotFoundError(f"Group {uuid} not found")
        return GroupResponse(
            uuid=group.uuid,
            name=group.name,
            description=group.description,
            permission_uuids=[p.uuid for p in group.permissions],
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    async def list_all(
        self, session: AsyncSession, params: PaginationParams
    ) -> GroupListResponse:
        items, total_pages, total_items = await self._repo.search(
            session,
            page=params.page,
            page_size=params.page_size,
            search_value=params.search,
        )
        return GroupListResponse(
            items=[
                GroupResponse(
                    uuid=g.uuid,
                    name=g.name,
                    description=g.description,
                    permission_uuids=[p.uuid for p in g.permissions],
                    created_at=g.created_at,
                    updated_at=g.updated_at,
                )
                for g in items
            ],
            total=total_items,
            page=params.page,
            pages=total_pages,
        )

    async def update(
        self, session: AsyncSession, uuid: UUID, body: GroupUpdateRequest
    ) -> GroupResponse:
        group = await self._repo.get_by_id(session, uuid)
        if not group:
            raise NotFoundError(f"Group {uuid} not found")

        update_data = body.model_dump(exclude={"permission_uuids"}, exclude_none=True)
        if update_data:
            await self._repo.update(session, group, **update_data)

        if body.permission_uuids is not None:
            await self._repo.assign_permissions(
                session, uuid, set(body.permission_uuids)
            )

        return await self.get_by(session, uuid)

    async def delete(self, session: AsyncSession, uuid: UUID) -> None:
        group = await self._repo.get_by_id(session, uuid)
        if not group:
            raise NotFoundError(f"Group {uuid} not found")
        await self._repo.delete(session, group)
