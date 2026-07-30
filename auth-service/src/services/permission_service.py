from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError
from src.models.permission import Permission
from src.repositories.permission_repository import PermissionRepository
from src.schemes.rbac import (
    PaginationParams,
    PermissionCreateRequest,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdateRequest,
)


class PermissionService:
    def __init__(self, repo: PermissionRepository) -> None:
        self._repo = repo

    async def create(
        self, session: AsyncSession, body: PermissionCreateRequest
    ) -> PermissionResponse:
        permission = Permission(**body.model_dump())
        result = await self._repo.create(session, permission)
        return PermissionResponse.model_validate(result)

    async def get_by(
        self, session: AsyncSession, uuid: UUID
    ) -> PermissionResponse:
        result = await self._repo.get_by_id(session, uuid)
        if not result:
            raise NotFoundError(f"Permission {uuid} not found")
        return PermissionResponse.model_validate(result)

    async def list_all(
        self, session: AsyncSession, params: PaginationParams
    ) -> PermissionListResponse:
        items, total_pages, total_items = await self._repo.search(
            session,
            page=params.page,
            page_size=params.page_size,
            search_value=params.search,
        )
        return PermissionListResponse(
            items=[PermissionResponse.model_validate(p) for p in items],
            total=total_items,
            page=params.page,
            pages=total_pages,
        )

    async def update(
        self, session: AsyncSession, uuid: UUID, body: PermissionUpdateRequest
    ) -> PermissionResponse:
        permission = await self._repo.get_by_id(session, uuid)
        if not permission:
            raise NotFoundError(f"Permission {uuid} not found")
        update_data = body.model_dump(exclude_none=True)
        result = await self._repo.update(session, permission, **update_data)
        return PermissionResponse.model_validate(result)

    async def delete(self, session: AsyncSession, uuid: UUID) -> None:
        permission = await self._repo.get_by_id(session, uuid)
        if not permission:
            raise NotFoundError(f"Permission {uuid} not found")
        await self._repo.delete(session, permission)
