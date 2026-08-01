import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    TokenPayload,
    get_token_payload,
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
from src.schemes.response.inventory import (
    LowStockItemResponse,
    PopularProductResponse,
    StockMovementResponse,
    StockResponse,
)
from src.services.inventory_service import InventoryService
from src.services.movement_service import MovementService

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get(
    "/low-stock",
    summary="List stock items at or below a threshold",
)
async def list_low_stock(
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    threshold: Annotated[int, Query(ge=0)] = 10,
) -> list[LowStockItemResponse]:
    """Used by scheduler-service's inventory alert job."""
    return await service.get_low_stock_items(session=session, threshold=threshold)


@router.get(
    "/popular",
    summary="List products ranked by reserved/shipped volume",
)
async def list_popular_products(
    service: Annotated[MovementService, Depends(Inject(MovementService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[PopularProductResponse]:
    """Used by scheduler-service's cache warmup job.

    Popularity is a proxy from inventory-service's own movement audit trail
    (reserved/shipped quantity) — this service has no visibility into orders
    or sales data, which live in order-service.
    """
    return await service.list_popular_products(session=session, limit=limit)


@router.get(
    "/",
    summary="Check stock levels",
)
async def check_stock(
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    product_id: Annotated[uuid.UUID, Query()],
    warehouse_id: Annotated[uuid.UUID, Query()],
) -> StockResponse:
    """Check stock levels for a product at a warehouse."""
    return await service.check_stock(
        session=session,
        request=StockCheckRequest(product_id=product_id, warehouse_id=warehouse_id),
    )


@router.get(
    "/by-product/{product_id}",
    summary="Check stock across all warehouses for a product",
)
async def check_stock_by_product(
    product_id: uuid.UUID,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    quantity: Annotated[int, Query(gt=0)],
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
        msg = f"No warehouse has {quantity} available for product {product_id}"
        raise NotFoundError(msg)
    return result


@router.post(
    "/reserve-by-product",
    summary="Reserve stock for a product, picking the warehouse automatically",
)
async def reserve_stock_by_product(
    request: ReserveByProductRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Reserve stock without the caller picking a warehouse.

    Response includes `warehouse_id` — the caller (order-service) must store
    it so a later release() targets the same warehouse the reservation came
    from.
    """
    return await service.reserve_by_product(session=session, request=request)


@router.post(
    "/reserve",
    summary="Reserve stock",
)
async def reserve_stock(
    request: ReserveRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Reserve stock for a product at a warehouse."""
    return await service.reserve(session=session, request=request)


@router.post(
    "/release",
    summary="Release stock",
)
async def release_stock(
    request: ReleaseRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Release previously reserved stock."""
    return await service.release(session=session, request=request)


@router.post(
    "/receive",
    summary="Receive stock",
)
async def receive_stock(
    request: ReceiptRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Receive new stock into a warehouse."""
    return await service.receive(session=session, request=request)


@router.post(
    "/ship",
    summary="Ship stock",
)
async def ship_stock(
    request: ShipRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Ship stock out of a warehouse."""
    return await service.ship(session=session, request=request)


@router.post(
    "/adjust",
    summary="Adjust stock",
)
async def adjust_stock(
    request: AdjustRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Adjust stock levels for a product."""
    return await service.adjust(session=session, request=request)


@router.post(
    "/return",
    summary="Return stock",
)
async def return_stock(
    request: ReceiptRequest,
    service: Annotated[InventoryService, Depends(Inject(InventoryService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> StockResponse:
    """Process a stock return into a warehouse."""
    return await service.return_stock(session=session, request=request)


@router.get(
    "/movements",
    summary="List stock movements",
)
async def list_movements(
    service: Annotated[MovementService, Depends(Inject(MovementService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    stock_item_id: Annotated[uuid.UUID, Query()],
    movement_type: Annotated[str | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[StockMovementResponse]:
    """List stock movements for a stock item with optional filtering."""
    return await service.list_by_stock_item(
        session=session,
        stock_item_id=stock_item_id,
        movement_type=movement_type,
        offset=offset,
        limit=limit,
    )
