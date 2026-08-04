from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.depends import Inject, _require_admin, get_service_session
from src.schemes.rbac import (
    PaginationParams,
    PermissionCreateRequest,
    PermissionListResponse,
    PermissionResponse,
    PermissionUpdateRequest,
)
from src.services.permission_service import PermissionService

router = APIRouter(
    prefix="/auth",
    tags=["permissions"],
    dependencies=[Depends(_require_admin)],
)

PermissionIdPath = Annotated[
    UUID,
    Path(
        description="Permission id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000003"],
    ),
]


@router.get(
    "",
    summary="List permissions",
)
async def list_permissions(
    params: Annotated[PaginationParams, Depends()],
    service: Annotated[PermissionService, Depends(Inject(PermissionService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> PermissionListResponse:
    """List all permissions with pagination."""
    return await service.list_all(session, params)


@router.post(
    "",
    status_code=201,
    summary="Create permission",
)
async def create_permission(
    body: PermissionCreateRequest,
    service: Annotated[PermissionService, Depends(Inject(PermissionService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> PermissionResponse:
    """Create a new permission with the specified attributes."""
    return await service.create(session, body)


@router.get(
    "/{permission_id}",
    summary="Get permission",
)
async def get_permission(
    permission_id: PermissionIdPath,
    service: Annotated[PermissionService, Depends(Inject(PermissionService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> PermissionResponse:
    """Get a single permission by its id."""
    return await service.get_by(session, permission_id)


@router.put(
    "/{permission_id}",
    summary="Update permission",
)
async def update_permission(
    permission_id: PermissionIdPath,
    body: PermissionUpdateRequest,
    service: Annotated[PermissionService, Depends(Inject(PermissionService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> PermissionResponse:
    """Update an existing permission by its id."""
    return await service.update(session, permission_id, body)


@router.delete(
    "/{permission_id}",
    summary="Delete permission",
)
async def delete_permission(
    permission_id: PermissionIdPath,
    service: Annotated[PermissionService, Depends(Inject(PermissionService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> Response:
    """Delete a permission by its id."""
    await service.delete(session, permission_id)
    return Response(status_code=204)
