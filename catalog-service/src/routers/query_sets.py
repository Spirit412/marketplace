import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.auth import (
    Permission,
    TokenPayload,
    get_token_payload,
    require_permission,
)
from src.core.database import get_async_session
from src.depends import Inject
from src.schemes.request.query_set import CreateQuerySetRequest, UpdateQuerySetRequest
from src.schemes.response.query_set import QuerySetListResponse, QuerySetResponse
from src.services.query_set_service import QuerySetService

router = APIRouter(prefix="/query-sets", tags=["query-sets"])


@router.post(
    "/",
    response_model=QuerySetResponse,
    status_code=201,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Create query set",
)
async def create_query_set(
    body: CreateQuerySetRequest,
    service: Annotated[QuerySetService, Depends(Inject(QuerySetService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> QuerySetResponse:
    """Create a new query set for the authenticated seller."""
    qs = await service.create(
        session,
        seller_id=uuid.UUID(token_payload.user_uuid),
        name=body.name,
        data=body.data,
        displayed_fields=body.displayed_fields,
        tags=body.tags,
    )
    return QuerySetResponse.model_validate(qs)


@router.get(
    "/{query_set_id}",
    response_model=QuerySetResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
    summary="Get query set by ID",
)
async def get_query_set(
    query_set_id: uuid.UUID,
    service: Annotated[QuerySetService, Depends(Inject(QuerySetService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> QuerySetResponse:
    """Get a single query set by ID."""
    qs = await service.get_by_id(session, query_set_id)
    if qs is None:
        raise HTTPException(status_code=404, detail="Query set not found")
    return QuerySetResponse.model_validate(qs)


@router.put(
    "/{query_set_id}",
    response_model=QuerySetResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Update query set",
)
async def update_query_set(
    query_set_id: uuid.UUID,
    body: UpdateQuerySetRequest,
    service: Annotated[QuerySetService, Depends(Inject(QuerySetService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> QuerySetResponse:
    """Update an existing query set by ID."""
    qs = await service.update(
        session,
        query_set_id=query_set_id,
        **body.model_dump(exclude_none=True),
    )
    if qs is None:
        raise HTTPException(status_code=404, detail="Query set not found")
    return QuerySetResponse.model_validate(qs)


@router.delete(
    "/{query_set_id}",
    status_code=204,
    response_model=None,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Delete query set",
)
async def delete_query_set(
    query_set_id: uuid.UUID,
    service: Annotated[QuerySetService, Depends(Inject(QuerySetService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> None:
    """Delete a query set by ID."""
    deleted = await service.delete(session, query_set_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Query set not found")


@router.post(
    "/{query_set_id}/favorite",
    response_model=QuerySetResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
    summary="Toggle query set favorite",
)
async def toggle_favorite(
    query_set_id: uuid.UUID,
    service: Annotated[QuerySetService, Depends(Inject(QuerySetService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> QuerySetResponse:
    """Toggle the favorite status of a query set."""
    qs = await service.toggle_favorite(session, query_set_id)
    if qs is None:
        raise HTTPException(status_code=404, detail="Query set not found")
    return QuerySetResponse.model_validate(qs)


@router.get(
    "/system/list",
    response_model=list[QuerySetResponse],
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
    summary="List system query sets",
)
async def get_system_query_sets(
    service: Annotated[QuerySetService, Depends(Inject(QuerySetService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> list[QuerySetResponse]:
    """List all system-defined query sets."""
    system_sets = await service.get_system(session)
    return [QuerySetResponse.model_validate(qs) for qs in system_sets]


@router.get(
    "/",
    response_model=QuerySetListResponse,
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
    summary="List query sets",
)
async def list_query_sets(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[QuerySetService, Depends(Inject(QuerySetService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    page: int = 1,
    page_size: int = 20,
) -> QuerySetListResponse:
    """List query sets for the authenticated seller with pagination."""
    items, total = await service.get_by_seller(
        session,
        seller_id=uuid.UUID(token_payload.user_uuid),
        page=page,
        page_size=page_size,
    )
    return QuerySetListResponse(
        items=[QuerySetResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )
