from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.depends import Inject, _require_admin, get_service_session
from src.schemes.rbac import (
    PaginationParams,
    RoleCreateRequest,
    RoleListResponse,
    RoleResponse,
    RoleUpdateRequest,
)
from src.services.role_service import RoleService

router = APIRouter(
    prefix="/auth",
    tags=["roles"],
    dependencies=[Depends(_require_admin)],
)

RoleIdPath = Annotated[
    UUID,
    Path(
        description="Role id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000001"],
    ),
]


@router.get(
    "",
    summary="List roles",
)
async def list_roles(
    params: Annotated[PaginationParams, Depends()],
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> RoleListResponse:
    """List all roles with pagination."""
    return await service.list_all(session, params)


@router.post(
    "",
    status_code=201,
    summary="Create role",
)
async def create_role(
    body: RoleCreateRequest,
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> RoleResponse:
    """Create a new role with the specified attributes."""
    return await service.create(session, body)


@router.get(
    "/{role_id}",
    summary="Get role",
)
async def get_role(
    role_id: RoleIdPath,
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> RoleResponse:
    """Get a single role by its id."""
    return await service.get_by(session, role_id)


@router.put(
    "/{role_id}",
    summary="Update role",
)
async def update_role(
    role_id: RoleIdPath,
    body: RoleUpdateRequest,
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> RoleResponse:
    """Update an existing role by its id."""
    return await service.update(session, role_id, body)


@router.delete(
    "/{role_id}",
    summary="Delete role",
)
async def delete_role(
    role_id: RoleIdPath,
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> Response:
    """Delete a role by its id."""
    await service.delete(session, role_id)
    return Response(status_code=204)
