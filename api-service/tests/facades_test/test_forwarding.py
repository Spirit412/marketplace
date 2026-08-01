"""Every facade must forward the caller's own Authorization header verbatim.

Never substitute a system/service token. Getting this wrong would let a
composed endpoint read another user's data by escalating to a
service-to-service identity instead of the actual caller's. See
PLAN_api-service.md's "Ключевое архитектурное решение".
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.facades.catalog import CatalogFacade
from src.facades.inventory import InventoryFacade
from src.facades.order import OrderFacade
from src.facades.payment import PaymentFacade

CALLER_TOKEN = "Bearer this-is-the-caller-own-token"


@pytest.mark.asyncio
async def test_catalog_facade_forwards_caller_token() -> None:
    facade = CatalogFacade(base_url="http://catalog")
    with patch.object(
        facade._client, "get", new=AsyncMock(return_value={"id": "p1"})
    ) as mock_get:
        await facade.get_product("p1", CALLER_TOKEN)

    assert mock_get.call_args.kwargs["headers"]["Authorization"] == CALLER_TOKEN


@pytest.mark.asyncio
async def test_inventory_facade_forwards_caller_token() -> None:
    facade = InventoryFacade(base_url="http://inventory")
    with patch.object(
        facade._client, "get", new=AsyncMock(return_value={"available": 5})
    ) as mock_get:
        await facade.check_stock_by_product("p1", CALLER_TOKEN)

    assert mock_get.call_args.kwargs["headers"]["Authorization"] == CALLER_TOKEN


@pytest.mark.asyncio
async def test_order_facade_forwards_caller_token() -> None:
    facade = OrderFacade(base_url="http://order")
    with patch.object(
        facade._client, "get", new=AsyncMock(return_value={"id": "o1"})
    ) as mock_get:
        await facade.get_order("o1", CALLER_TOKEN)

    assert mock_get.call_args.kwargs["headers"]["Authorization"] == CALLER_TOKEN


@pytest.mark.asyncio
async def test_payment_facade_forwards_caller_token() -> None:
    facade = PaymentFacade(base_url="http://payment")
    with patch.object(
        facade._client, "get", new=AsyncMock(return_value={"id": "pay1"})
    ) as mock_get:
        await facade.get_payment_by_order("o1", CALLER_TOKEN)

    assert mock_get.call_args.kwargs["headers"]["Authorization"] == CALLER_TOKEN


@pytest.mark.asyncio
async def test_catalog_facade_never_sends_a_system_token() -> None:
    """The regression this whole test file exists to catch.

    A facade that silently defaulted to (or fell back to) some other
    token — SYSTEM_TOKEN, a hardcoded string, `None` — would still "work"
    functionally (most downstream services grant SYSTEM_TOKEN broad
    access) while quietly breaking per-user authorization. Asserting the
    literal forwarded value, not just "some Authorization header was
    sent", is the point.
    """
    facade = CatalogFacade(base_url="http://catalog")
    with patch.object(
        facade._client, "get", new=AsyncMock(return_value={"id": "p1"})
    ) as mock_get:
        await facade.get_product("p1", CALLER_TOKEN)

    sent = mock_get.call_args.kwargs["headers"]["Authorization"]
    assert sent == CALLER_TOKEN
    assert "SYSTEM_TOKEN" not in sent
