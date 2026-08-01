from unittest.mock import AsyncMock

import pytest

from src.exceptions import NotFoundError
from src.routers.orders import get_order_full


class _StubRequest:
    def __init__(self, authorization: str = "Bearer caller-token") -> None:
        self.headers = {"Authorization": authorization}


ORDER = {
    "id": "019f0000-0000-0000-0000-000000000010",
    "user_id": "019f0000-0000-0000-0000-000000000011",
    "status": "confirmed",
    "items": [],
    "subtotal": 1000,
    "tax": 200,
    "discount": 0,
    "shipping": 0,
    "total": 1200,
    "currency": "RUB",
    "payment_method": "MOCK",
    "shipping_address": None,
    "notes": None,
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

PAYMENT = {
    "id": "019f0000-0000-0000-0000-000000000020",
    "status": "SUCCEEDED",
    "amount": 1200,
    "currency": "RUB",
    "gateway": "mock",
    "gateway_payment_id": "mock_pi_1",
}


@pytest.mark.asyncio
async def test_composes_order_and_payment() -> None:
    order_facade = AsyncMock(get_order=AsyncMock(return_value=ORDER))
    payment_facade = AsyncMock(get_payment_by_order=AsyncMock(return_value=PAYMENT))

    result = await get_order_full(
        ORDER["id"], _StubRequest(), order_facade, payment_facade
    )

    assert str(result.id) == ORDER["id"]
    assert result.payment is not None
    assert result.payment.status == "SUCCEEDED"


@pytest.mark.asyncio
async def test_pending_order_has_no_payment_yet() -> None:
    """No payment is an expected state, not an error.

    See the docstring on get_order_full and PaymentFacade.get_payment_by_order.
    """
    order_facade = AsyncMock(get_order=AsyncMock(return_value=ORDER))
    payment_facade = AsyncMock(get_payment_by_order=AsyncMock(return_value=None))

    result = await get_order_full(
        ORDER["id"], _StubRequest(), order_facade, payment_facade
    )

    assert result.payment is None


@pytest.mark.asyncio
async def test_payment_outage_degrades_instead_of_failing() -> None:
    """Same principle as storefront's inventory-outage test.

    payment-service being unreachable shouldn't take down an order page
    that's otherwise perfectly servable — see get_order_full's docstring.
    """
    order_facade = AsyncMock(get_order=AsyncMock(return_value=ORDER))
    payment_facade = AsyncMock(
        get_payment_by_order=AsyncMock(side_effect=ConnectionError("payment is down"))
    )

    result = await get_order_full(
        ORDER["id"], _StubRequest(), order_facade, payment_facade
    )

    assert str(result.id) == ORDER["id"]
    assert result.payment is None


@pytest.mark.asyncio
async def test_missing_or_not_own_order_is_404() -> None:
    """order-service's 404 covers both "doesn't exist" and "not the caller's own".

    See PLAN_order-service.md's IDOR note — api-service must not turn that
    back into something more revealing.
    """
    order_facade = AsyncMock(get_order=AsyncMock(return_value=None))
    payment_facade = AsyncMock(get_payment_by_order=AsyncMock(return_value=None))

    with pytest.raises(NotFoundError):
        await get_order_full(
            "someone-elses-order", _StubRequest(), order_facade, payment_facade
        )
