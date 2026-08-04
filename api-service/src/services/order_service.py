"""Business logic for the order+payment composed endpoint."""

import asyncio
from typing import Any

from src.exceptions import NotFoundError
from src.facades.order import OrderFacade
from src.facades.payment import PaymentFacade
from src.schemes.response.order import OrderFullResponse, PaymentSummary


class OrderService:
    def __init__(
        self, order_facade: OrderFacade, payment_facade: PaymentFacade
    ) -> None:
        self._order_facade = order_facade
        self._payment_facade = payment_facade

    async def get_order_full(
        self, order_id: str, authorization: str
    ) -> OrderFullResponse:
        """Order detail + payment status in one call.

        The two calls an order-tracking page always needs, issued in
        parallel instead of one after another.

        Order-service's 404 (not found, or exists but isn't the caller's
        own — see PLAN_order-service.md's IDOR note) is authoritative and
        propagates as-is — without an order there's nothing to compose.
        Payment is the non-critical side of this composition, same as
        inventory is for get_product_card: a missing payment is expected (a
        `pending` order has none yet) and payment-service being
        unreachable degrades to `payment: None` rather than failing the
        whole request — an order page is still useful without live
        payment status.
        """
        gather_results: tuple[
            dict[str, Any] | BaseException | None, ...
        ] = await asyncio.gather(
            self._order_facade.get_order(order_id, authorization),
            self._payment_facade.get_payment_by_order(order_id, authorization),
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
