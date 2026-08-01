import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth_middleware import _get_auth_state
from src.core.auth import TokenPayload, get_token_payload
from src.core.database import get_async_session
from src.depends import Inject, enforce_order_rate_limit
from src.schemes.request.order import CreateOrderRequest
from src.schemes.response.order import (
    OrderListResponse,
    OrderResponse,
)
from src.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(enforce_order_rate_limit)],
    summary="Create order",
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
        user_id=uuid.UUID(token_payload.user_id),
        shipping_address=body.shipping_address,
        payment_method=body.payment_method.value,
        tax_strategy=body.tax_strategy.value,
        idempotency_key=idempotency_key,
        notes=body.notes,
    )
    return OrderResponse.model_validate(order)


@router.get(
    "/",
    summary="List user orders",
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
        user_id=uuid.UUID(token_payload.user_id),
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
    "/pending",
    summary="List pending orders older than a threshold (internal, for the scheduler)",
)
async def get_pending_orders(
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[OrderService, Depends(Inject(OrderService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    older_than_minutes: Annotated[int, Query(ge=1)] = 30,
) -> list[OrderResponse]:
    """Orders still 'pending' after older_than_minutes.

    Used by the scheduler's cancel_unpaid_orders job. Must be declared
    before /{order_uuid} — a static segment after a parameterised one
    would be swallowed as a (invalid) UUID path param instead of matching
    here.
    """
    orders = await service.get_expired_orders(
        session=session, expiration_minutes=older_than_minutes
    )
    return [OrderResponse.model_validate(order) for order in orders]


@router.get(
    "/{order_uuid}",
    summary="Get order by ID",
)
async def get_order(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    order_uuid: uuid.UUID,
    service: Annotated[OrderService, Depends(Inject(OrderService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> OrderResponse:
    """Get a single order by UUID."""
    order = await service.get_order(
        session=session,
        order_uuid=order_uuid,
        user_id=uuid.UUID(token_payload.user_id),
    )
    return OrderResponse.model_validate(order)


@router.post(
    "/{order_uuid}/cancel",
    summary="Cancel order",
)
async def cancel_order(
    request: Request,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    order_uuid: uuid.UUID,
    service: Annotated[OrderService, Depends(Inject(OrderService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> OrderResponse:
    """Cancel an order.

    The owner, or a privileged caller (system/admin, e.g. the scheduler's
    cancel_unpaid_orders job).
    """
    auth_state = _get_auth_state(request)
    order = await service.cancel_order(
        session=session,
        order_uuid=order_uuid,
        user_id=uuid.UUID(token_payload.user_id),
        caller_is_privileged=auth_state.is_admin or auth_state.role == "system",
    )
    return OrderResponse.model_validate(order)
