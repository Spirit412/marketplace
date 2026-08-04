from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.core.database import get_async_session
from src.depends import Inject
from src.schemes.request.inventory import WarehouseCreateRequest, WarehouseUpdateRequest
from src.schemes.response.inventory import WarehouseResponse
from src.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["warehouses"])

WarehouseIdPath = Annotated[
    UUID,
    Path(
        description="Warehouse id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000080"],
    ),
]


@router.post(
    "/",
    status_code=201,
    summary="Create warehouse",
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
        seller_id=UUID(token_payload.user_id),
    )


@router.get(
    "/",
    summary="List warehouses",
)
async def list_warehouses(
    service: Annotated[WarehouseService, Depends(Inject(WarehouseService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    offset: Annotated[int, Query(ge=0, description="Rows to skip.")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max rows to return.")] = 50,
) -> list[WarehouseResponse]:
    """List warehouses for the authenticated seller with pagination."""
    return await service.list(
        session=session,
        seller_id=UUID(token_payload.user_id),
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{warehouse_id}",
    summary="Get warehouse by ID",
)
async def get_warehouse(
    warehouse_id: WarehouseIdPath,
    service: Annotated[WarehouseService, Depends(Inject(WarehouseService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> WarehouseResponse:
    """Get a single warehouse by ID."""
    return await service.get(
        session=session,
        warehouse_id=warehouse_id,
        seller_id=UUID(token_payload.user_id),
    )


@router.patch(
    "/{warehouse_id}",
    summary="Update warehouse",
)
async def update_warehouse(
    warehouse_id: WarehouseIdPath,
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
        seller_id=UUID(token_payload.user_id),
    )


@router.delete(
    "/{warehouse_id}",
    status_code=204,
    response_model=None,
    summary="Delete warehouse",
)
async def delete_warehouse(
    warehouse_id: WarehouseIdPath,
    service: Annotated[WarehouseService, Depends(Inject(WarehouseService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> None:
    """Delete a warehouse by ID."""
    await service.delete(
        session=session,
        warehouse_id=warehouse_id,
        seller_id=UUID(token_payload.user_id),
    )
