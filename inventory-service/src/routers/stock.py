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
from src.exceptions import NotFoundError
from src.schemes.request.inventory import (
    AdjustRequest,
    ReceiptRequest,
    ReleaseRequest,
    ReserveByProductRequest,
    ReserveRequest,
    ShipRequest,
    StockCheckByProductRequest,
    StockCheckRequest,
)
from src.schemes.response.inventory import StockMovementResponse, StockResponse
from src.services.inventory_service import InventoryService
from src.services.movement_service import MovementService

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get(
    "/",
    response_model=StockResponse,
    summary="Check stock levels",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def check_stock(
    product_id: uuid.UUID = Query(...),
    warehouse_id: uuid.UUID = Query(...),
    service: Annotated[InventoryService, Depends(Inject(InventoryService))] = None,
    session: Annotated[AsyncSession, Depends(get_async_session)] = None,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)] = None,
) -> StockResponse:
    """Check stock levels for a product at a warehouse."""
    return await service.check_stock(
        session=session,
        request=StockCheckRequest(product_id=product_id, warehouse_id=warehouse_id),
    )


@router.get(
    "/by-product/{product_id}",
    response_model=StockResponse,
    summary="Check stock across all warehouses for a product",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def check_stock_by_product(
    product_id: uuid.UUID,
    quantity: int = Query(gt=0),
    service: Annotated[InventoryService, Depends(Inject(InventoryService))] = None,
    session: Annotated[AsyncSession, Depends(get_async_session)] = None,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)] = None,
) -> StockResponse:
    """Find a warehouse with enough stock, without the caller knowing which one.

    Used by order-service, which tracks products and quantities but not
    warehouses. 404 if no single warehouse can satisfy the quantity.
    """
    result = await service.check_stock_by_product(
        session=session,
        request=StockCheckByProductRequest(product_id=product_id, quantity=quantity),
    )
    if result is None:
        raise NotFoundError(
            f"No warehouse has {quantity} available for product {product_id}"
        )
    return result


@router.post(
    "/reserve-by-product",
    response_model=StockResponse,
    summary="Reserve stock for a product, picking the warehouse automatically",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def reserve_stock_by_product(
    request: ReserveByProductRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Reserve stock without the caller picking a warehouse.

    Response includes `warehouse_id` — the caller (order-service) must store
    it so a later release() targets the same warehouse the reservation came
    from.
    """
    return await service.reserve_by_product(session=session, request=request)


@router.post(
    "/reserve",
    response_model=StockResponse,
    summary="Reserve stock",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def reserve_stock(
    request: ReserveRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Reserve stock for a product at a warehouse."""
    return await service.reserve(session=session, request=request)


@router.post(
    "/release",
    response_model=StockResponse,
    summary="Release stock",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def release_stock(
    request: ReleaseRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Release previously reserved stock."""
    return await service.release(session=session, request=request)


@router.post(
    "/receive",
    response_model=StockResponse,
    summary="Receive stock",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def receive_stock(
    request: ReceiptRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Receive new stock into a warehouse."""
    return await service.receive(session=session, request=request)


@router.post(
    "/ship",
    response_model=StockResponse,
    summary="Ship stock",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def ship_stock(
    request: ShipRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Ship stock out of a warehouse."""
    return await service.ship(session=session, request=request)


@router.post(
    "/adjust",
    response_model=StockResponse,
    summary="Adjust stock",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def adjust_stock(
    request: AdjustRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Adjust stock levels for a product."""
    return await service.adjust(session=session, request=request)


@router.post(
    "/return",
    response_model=StockResponse,
    summary="Return stock",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def return_stock(
    request: ReceiptRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Process a stock return into a warehouse."""
    return await service.return_stock(session=session, request=request)


@router.get(
    "/movements",
    response_model=list[StockMovementResponse],
    summary="List stock movements",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def list_movements(
    stock_item_id: uuid.UUID = Query(...),
    movement_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    service: Annotated[MovementService, Depends(Inject(MovementService))] = None,
    session: Annotated[AsyncSession, Depends(get_async_session)] = None,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)] = None,
) -> list[StockMovementResponse]:
    """List stock movements for a stock item with optional filtering."""
    return await service.list_by_stock_item(
        session=session,
        stock_item_id=stock_item_id,
        movement_type=movement_type,
        offset=offset,
        limit=limit,
    )
