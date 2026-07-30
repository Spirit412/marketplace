import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.auth import Permission, require_permission
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


@router.get(
    "/roles",
    response_model=RoleListResponse,
    summary="List roles",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def list_roles(
    params: Annotated[PaginationParams, Depends()],
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> RoleListResponse:
    """List all roles with pagination."""
    return await service.list_all(session, params)


@router.post(
    "/roles",
    response_model=RoleResponse,
    status_code=201,
    summary="Create role",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def create_role(
    body: RoleCreateRequest,
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> RoleResponse:
    """Create a new role with the specified attributes."""
    return await service.create(session, body)


@router.get(
    "/roles/{role_uuid}",
    response_model=RoleResponse,
    summary="Get role",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_role(
    role_uuid: uuid.UUID,
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> RoleResponse:
    """Get a single role by its UUID."""
    return await service.get_by(session, role_uuid)


@router.put(
    "/roles/{role_uuid}",
    response_model=RoleResponse,
    summary="Update role",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def update_role(
    role_uuid: uuid.UUID,
    body: RoleUpdateRequest,
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> RoleResponse:
    """Update an existing role by its UUID."""
    return await service.update(session, role_uuid, body)


@router.delete(
    "/roles/{role_uuid}",
    status_code=204,
    response_class=Response,
    summary="Delete role",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.ALL))],
)
async def delete_role(
    role_uuid: uuid.UUID,
    service: Annotated[RoleService, Depends(Inject(RoleService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> Response:
    """Delete a role by its UUID."""
    await service.delete(session, role_uuid)
    return Response(status_code=204)
