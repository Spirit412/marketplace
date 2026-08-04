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
        if body.group_ids:
            await self._repo.assign_groups(session, result.id, set(body.group_ids))
        return RoleResponse.model_validate(result)

    async def get_by(self, session: AsyncSession, role_id: UUID) -> RoleResponse:
        role = await self._repo.get_with_groups(session, role_id)
        if not role:
            raise NotFoundError(f"Role {role_id} not found")
        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_admin=role.is_admin,
            group_ids=[g.id for g in role.groups],
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
                    id=r.id,
                    name=r.name,
                    description=r.description,
                    is_admin=r.is_admin,
                    group_ids=[],
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
        self, session: AsyncSession, role_id: UUID, body: RoleUpdateRequest
    ) -> RoleResponse:
        role = await self._repo.get_by_id(session, role_id)
        if not role:
            raise NotFoundError(f"Role {role_id} not found")

        update_data = body.model_dump(exclude={"group_ids"}, exclude_none=True)
        if update_data:
            await self._repo.update(session, role, **update_data)

        if body.group_ids is not None:
            await self._repo.assign_groups(session, role_id, set(body.group_ids))

        return await self.get_by(session, role_id)

    async def delete(self, session: AsyncSession, role_id: UUID) -> None:
        role = await self._repo.get_by_id(session, role_id)
        if not role:
            raise NotFoundError(f"Role {role_id} not found")
        await self._repo.delete(session, role)
