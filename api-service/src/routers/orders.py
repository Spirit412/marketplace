import asyncio
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from src.depends import Inject
from src.exceptions import NotFoundError
from src.facades.order import OrderFacade
from src.facades.payment import PaymentFacade
from src.schemes.response.order import OrderFullResponse, PaymentSummary

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get(
    "/{order_id}/full",
    summary="Order + payment status in one call",
)
async def get_order_full(
    order_id: str,
    request: Request,
    order_facade: Annotated[OrderFacade, Depends(Inject(OrderFacade))],
    payment_facade: Annotated[PaymentFacade, Depends(Inject(PaymentFacade))],
) -> OrderFullResponse:
    """Order detail + payment status in one call.

    The two calls an order-tracking page always needs, issued in parallel
    instead of one after another.

    Order-service's 404 (not found, or exists but isn't the caller's own —
    see PLAN_order-service.md's IDOR note) is authoritative and propagates
    as-is — without an order there's nothing to compose. Payment is the
    non-critical side of this composition, same as inventory is for
    get_storefront_product: a missing payment is expected (a `pending`
    order has none yet) and payment-service being unreachable degrades to
    `payment: None` rather than failing the whole request — an order page
    is still useful without live payment status.
    """
    authorization = request.headers.get("Authorization", "")

    gather_results: tuple[
        dict[str, Any] | BaseException | None, ...
    ] = await asyncio.gather(
        order_facade.get_order(order_id, authorization),
        payment_facade.get_payment_by_order(order_id, authorization),
        return_exceptions=True,
    )
    order_result, payment_result = gather_results
    if isinstance(order_result, BaseException):
        raise order_result
    if order_result is None:
        raise NotFoundError(f"Order {order_id} not found")

    payment = None if isinstance(payment_result, BaseException) else payment_result

    return OrderFullResponse(
        **order_result,
        payment=PaymentSummary(**payment) if payment else None,
    )
