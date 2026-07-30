import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
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
from src.schemes.request.order import CreateOrderRequest
from src.schemes.response.order import (
    OrderListResponse,
    OrderResponse,
)
from src.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=201,
    summary="Create order",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def create_order(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    body: CreateOrderRequest,
    service: Annotated[OrderService, Depends(Inject(OrderService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> OrderResponse:
    """Create a new order from the user's cart."""
    order = await service.create_order(
        session=session,
        user_uuid=uuid.UUID(token_payload.user_uuid),
        shipping_address=body.shipping_address,
        payment_method=body.payment_method.value,
        tax_strategy=body.tax_strategy.value,
        idempotency_key=idempotency_key,
        notes=body.notes,
    )
    return OrderResponse.model_validate(order)


@router.get(
    "/",
    response_model=OrderListResponse,
    summary="List user orders",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_orders(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[OrderService, Depends(Inject(OrderService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OrderListResponse:
    """Get user's orders (paginated)."""
    orders, total = await service.get_user_orders(
        session=session,
        user_uuid=uuid.UUID(token_payload.user_uuid),
        page=page,
        page_size=page_size,
    )
    return OrderListResponse(
        items=[OrderResponse.model_validate(order) for order in orders],
        total_count=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{order_uuid}",
    response_model=OrderResponse,
    summary="Get order by ID",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_order(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    order_uuid: uuid.UUID,
    service: Annotated[OrderService, Depends(Inject(OrderService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> OrderResponse:
    """Get a single order by UUID."""
    order = await service.get_order(session=session, order_uuid=order_uuid)
    return OrderResponse.model_validate(order)


@router.post(
    "/{order_uuid}/cancel",
    response_model=OrderResponse,
    summary="Cancel order",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def cancel_order(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    order_uuid: uuid.UUID,
    service: Annotated[OrderService, Depends(Inject(OrderService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> OrderResponse:
    """Cancel an order."""
    order = await service.cancel_order(
        session=session,
        order_uuid=order_uuid,
        user_uuid=uuid.UUID(token_payload.user_uuid),
    )
    return OrderResponse.model_validate(order)
