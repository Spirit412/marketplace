import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.auth import Permission, require_permission
from src.depends import Inject, _require_admin, get_service_session
from src.schemes.rbac import (
    GroupCreateRequest,
    GroupListResponse,
    GroupResponse,
    GroupUpdateRequest,
    PaginationParams,
)
from src.services.group_service import GroupService

router = APIRouter(
    prefix="/auth",
    tags=["groups"],
    dependencies=[Depends(_require_admin)],
)


@router.get(
    "/groups",
    response_model=GroupListResponse,
    summary="List groups",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def list_groups(
    params: Annotated[PaginationParams, Depends()],
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> GroupListResponse:
    """List all groups with pagination."""
    return await service.list_all(session, params)


@router.post(
    "/groups",
    response_model=GroupResponse,
    status_code=201,
    summary="Create group",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def create_group(
    body: GroupCreateRequest,
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> GroupResponse:
    """Create a new group with the specified attributes."""
    return await service.create(session, body)


@router.get(
    "/groups/{group_uuid}",
    response_model=GroupResponse,
    summary="Get group",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_group(
    group_uuid: uuid.UUID,
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> GroupResponse:
    """Get a single group by its UUID."""
    return await service.get_by(session, group_uuid)


@router.put(
    "/groups/{group_uuid}",
    response_model=GroupResponse,
    summary="Update group",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def update_group(
    group_uuid: uuid.UUID,
    body: GroupUpdateRequest,
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> GroupResponse:
    """Update an existing group by its UUID."""
    return await service.update(session, group_uuid, body)


@router.delete(
    "/groups/{group_uuid}",
    status_code=204,
    response_class=Response,
    summary="Delete group",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.ALL))],
)
async def delete_group(
    group_uuid: uuid.UUID,
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> Response:
    """Delete a group by its UUID."""
    await service.delete(session, group_uuid)
    return Response(status_code=204)
