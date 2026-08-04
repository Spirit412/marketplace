from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

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

GroupIdPath = Annotated[
    UUID,
    Path(
        description="Group id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000002"],
    ),
]


@router.get(
    "",
    summary="List groups",
)
async def list_groups(
    params: Annotated[PaginationParams, Depends()],
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> GroupListResponse:
    """List all groups with pagination."""
    return await service.list_all(session, params)


@router.post(
    "",
    status_code=201,
    summary="Create group",
)
async def create_group(
    body: GroupCreateRequest,
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> GroupResponse:
    """Create a new group with the specified attributes."""
    return await service.create(session, body)


@router.get(
    "/{group_id}",
    summary="Get group",
)
async def get_group(
    group_id: GroupIdPath,
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> GroupResponse:
    """Get a single group by its id."""
    return await service.get_by(session, group_id)


@router.put(
    "/{group_id}",
    summary="Update group",
)
async def update_group(
    group_id: GroupIdPath,
    body: GroupUpdateRequest,
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> GroupResponse:
    """Update an existing group by its id."""
    return await service.update(session, group_id, body)


@router.delete(
    "/{group_id}",
    summary="Delete group",
)
async def delete_group(
    group_id: GroupIdPath,
    service: Annotated[GroupService, Depends(Inject(GroupService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> Response:
    """Delete a group by its id."""
    await service.delete(session, group_id)
    return Response(status_code=204)
