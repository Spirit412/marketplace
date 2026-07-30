from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError
from src.models.role import Role
from src.repositories.role_repository import RoleRepository
from src.schemes.rbac import (
    PaginationParams,
    RoleCreateRequest,
    RoleListResponse,
    RoleResponse,
    RoleUpdateRequest,
)


class RoleService:
    def __init__(self, repo: RoleRepository) -> None:
        self._repo = repo

    async def create(
        self, session: AsyncSession, body: RoleCreateRequest
    ) -> RoleResponse:
        role = Role(
            name=body.name,
            description=body.description,
            is_admin=body.is_admin,
        )
        result = await self._repo.create(session, role)
        if body.group_uuids:
            await self._repo.assign_groups(
                session, result.uuid, set(body.group_uuids)
            )
        return RoleResponse.model_validate(result)

    async def get_by(self, session: AsyncSession, uuid: UUID) -> RoleResponse:
        role = await self._repo.get_with_groups(session, uuid)
        if not role:
            raise NotFoundError(f"Role {uuid} not found")
        return RoleResponse(
            uuid=role.uuid,
            name=role.name,
            description=role.description,
            is_admin=role.is_admin,
            group_uuids=[g.uuid for g in role.groups],
            created_at=role.created_at,
            updated_at=role.updated_at,
        )

    async def list_all(
        self, session: AsyncSession, params: PaginationParams
    ) -> RoleListResponse:
        items, total_pages, total_items = await self._repo.search(
            session,
            page=params.page,
            page_size=params.page_size,
            search_value=params.search,
        )
        return RoleListResponse(
            items=[
                RoleResponse(
                    uuid=r.uuid,
                    name=r.name,
                    description=r.description,
                    is_admin=r.is_admin,
                    group_uuids=[],
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
                for r in items
            ],
            total=total_items,
            page=params.page,
            pages=total_pages,
        )

    async def update(
        self, session: AsyncSession, uuid: UUID, body: RoleUpdateRequest
    ) -> RoleResponse:
        role = await self._repo.get_by_id(session, uuid)
        if not role:
            raise NotFoundError(f"Role {uuid} not found")

        update_data = body.model_dump(exclude={"group_uuids"}, exclude_none=True)
        if update_data:
            await self._repo.update(session, role, **update_data)

        if body.group_uuids is not None:
            await self._repo.assign_groups(
                session, uuid, set(body.group_uuids)
            )

        return await self.get_by(session, uuid)

    async def delete(self, session: AsyncSession, uuid: UUID) -> None:
        role = await self._repo.get_by_id(session, uuid)
        if not role:
            raise NotFoundError(f"Role {uuid} not found")
        await self._repo.delete(session, role)
