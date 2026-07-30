import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
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
from src.schemes.request.inventory import WarehouseCreateRequest, WarehouseUpdateRequest
from src.schemes.response.inventory import WarehouseResponse
from src.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


@router.post(
    "/",
    response_model=WarehouseResponse,
    status_code=201,
    summary="Create warehouse",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def create_warehouse(
    request: WarehouseCreateRequest,
    service: Annotated[WarehouseService, Depends(Inject(WarehouseService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> WarehouseResponse:
    """Create a new warehouse for the authenticated seller."""
    return await service.create(
        session=session,
        request=request,
        seller_id=uuid.UUID(token_payload.user_uuid),
    )


@router.get(
    "/",
    response_model=list[WarehouseResponse],
    summary="List warehouses",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def list_warehouses(
    service: Annotated[WarehouseService, Depends(Inject(WarehouseService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[WarehouseResponse]:
    """List warehouses for the authenticated seller with pagination."""
    return await service.list(
        session=session,
        seller_id=uuid.UUID(token_payload.user_uuid),
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    summary="Get warehouse by ID",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_warehouse(
    warehouse_id: uuid.UUID,
    service: Annotated[WarehouseService, Depends(Inject(WarehouseService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> WarehouseResponse:
    """Get a single warehouse by ID."""
    return await service.get(
        session=session,
        warehouse_id=warehouse_id,
        seller_id=uuid.UUID(token_payload.user_uuid),
    )


@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
    summary="Update warehouse",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def update_warehouse(
    warehouse_id: uuid.UUID,
    request: WarehouseUpdateRequest,
    service: Annotated[WarehouseService, Depends(Inject(WarehouseService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> WarehouseResponse:
    """Update an existing warehouse by ID."""
    return await service.update(
        session=session,
        warehouse_id=warehouse_id,
        request=request,
        seller_id=uuid.UUID(token_payload.user_uuid),
    )


@router.delete(
    "/{warehouse_id}",
    status_code=204,
    response_model=None,
    summary="Delete warehouse",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.ALL))],
)
async def delete_warehouse(
    warehouse_id: uuid.UUID,
    service: Annotated[WarehouseService, Depends(Inject(WarehouseService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> None:
    """Delete a warehouse by ID."""
    await service.delete(
        session=session,
        warehouse_id=warehouse_id,
        seller_id=uuid.UUID(token_payload.user_uuid),
    )
