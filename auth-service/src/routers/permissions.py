import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
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
    "/{perm_uuid}",
    summary="Get permission",
)
async def get_permission(
    perm_uuid: uuid.UUID,
    service: Annotated[PermissionService, Depends(Inject(PermissionService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> PermissionResponse:
    """Get a single permission by its UUID."""
    return await service.get_by(session, perm_uuid)


@router.put(
    "/{perm_uuid}",
    summary="Update permission",
)
async def update_permission(
    perm_uuid: uuid.UUID,
    body: PermissionUpdateRequest,
    service: Annotated[PermissionService, Depends(Inject(PermissionService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> PermissionResponse:
    """Update an existing permission by its UUID."""
    return await service.update(session, perm_uuid, body)


@router.delete(
    "/{perm_uuid}",
    summary="Delete permission",
)
async def delete_permission(
    perm_uuid: uuid.UUID,
    service: Annotated[PermissionService, Depends(Inject(PermissionService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> Response:
    """Delete a permission by its UUID."""
    await service.delete(session, perm_uuid)
    return Response(status_code=204)
