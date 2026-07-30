"""Integration tests for order endpoints."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_order_success(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test successful order creation."""
    order_id = str(uuid.uuid4())
    mock_order = MagicMock()
    mock_order.id = uuid.UUID(order_id)
    mock_order.user_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    mock_order.status = "pending"
    mock_order.items = []
    mock_order.subtotal = 0
    mock_order.tax = 0
    mock_order.discount = 0
    mock_order.shipping = 0
    mock_order.total = 0
    mock_order.currency = "RUB"
    mock_order.payment_method = "MOCK"
    mock_order.shipping_address = {"city": "Moscow"}
    mock_order.notes = None
    mock_order.idempotency_key = None
    mock_order.created_at = __import__("datetime").datetime(2024, 1, 1)
    mock_order.updated_at = __import__("datetime").datetime(2024, 1, 1)

    with (
        patch("src.routers.orders._get_order_service") as mock_get_svc,
    ):
        mock_svc = MagicMock()
        mock_svc.create_order = AsyncMock(return_value=mock_order)
        mock_get_svc.return_value = mock_svc

        response = await async_client.post(
            "/orders",
            json={
                "shipping_address": {"city": "Moscow"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers=auth_headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == order_id
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_order_idempotency(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test idempotency: duplicate key returns same order."""
    order_id = str(uuid.uuid4())
    idem_key = "test-idempotency-key"

    mock_order = MagicMock()
    mock_order.id = uuid.UUID(order_id)
    mock_order.user_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    mock_order.status = "pending"
    mock_order.items = []
    mock_order.subtotal = 100
    mock_order.tax = 20
    mock_order.discount = 0
    mock_order.shipping = 0
    mock_order.total = 120
    mock_order.currency = "RUB"
    mock_order.payment_method = "MOCK"
    mock_order.shipping_address = {"city": "Moscow"}
    mock_order.notes = None
    mock_order.idempotency_key = idem_key
    mock_order.created_at = __import__("datetime").datetime(2024, 1, 1)
    mock_order.updated_at = __import__("datetime").datetime(2024, 1, 1)

    with patch("src.routers.orders._get_order_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.create_order = AsyncMock(return_value=mock_order)
        mock_get_svc.return_value = mock_svc

        response1 = await async_client.post(
            "/orders",
            json={
                "shipping_address": {"city": "Moscow"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers={
                **auth_headers,
                "Idempotency-Key": idem_key,
            },
        )
        response2 = await async_client.post(
            "/orders",
            json={
                "shipping_address": {"city": "Moscow"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers={
                **auth_headers,
                "Idempotency-Key": idem_key,
            },
        )

    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response1.json()["id"] == response2.json()["id"]


@pytest.mark.asyncio
async def test_get_orders_empty(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test retrieving empty order list."""
    with patch("src.routers.orders._get_order_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.get_user_orders = AsyncMock(return_value=([], 0))
        mock_get_svc.return_value = mock_svc

        response = await async_client.get(
            "/orders",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total_count"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20


@pytest.mark.asyncio
async def test_get_orders_with_items(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test retrieving orders with items."""
    order_id = str(uuid.uuid4())

    mock_order = MagicMock()
    mock_order.id = uuid.UUID(order_id)
    mock_order.user_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    mock_order.status = "pending"
    mock_order.items = []
    mock_order.subtotal = 0
    mock_order.tax = 0
    mock_order.discount = 0
    mock_order.shipping = 0
    mock_order.total = 0
    mock_order.currency = "RUB"
    mock_order.payment_method = None
    mock_order.shipping_address = None
    mock_order.notes = None
    mock_order.idempotency_key = None
    mock_order.created_at = __import__("datetime").datetime(2024, 1, 1)
    mock_order.updated_at = __import__("datetime").datetime(2024, 1, 1)

    with patch("src.routers.orders._get_order_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.get_user_orders = AsyncMock(return_value=([mock_order], 1))
        mock_get_svc.return_value = mock_svc

        response = await async_client.get("/orders", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total_count"] == 1


@pytest.mark.asyncio
async def test_get_order_by_uuid(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test getting a single order."""
    order_id = str(uuid.uuid4())

    mock_order = MagicMock()
    mock_order.id = uuid.UUID(order_id)
    mock_order.user_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    mock_order.status = "pending"
    mock_order.items = []
    mock_order.subtotal = 0
    mock_order.tax = 0
    mock_order.discount = 0
    mock_order.shipping = 0
    mock_order.total = 0
    mock_order.currency = "RUB"
    mock_order.payment_method = None
    mock_order.shipping_address = None
    mock_order.notes = None
    mock_order.idempotency_key = None
    mock_order.created_at = __import__("datetime").datetime(2024, 1, 1)
    mock_order.updated_at = __import__("datetime").datetime(2024, 1, 1)

    with patch("src.routers.orders._get_order_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.get_order = AsyncMock(return_value=mock_order)
        mock_get_svc.return_value = mock_svc

        response = await async_client.get(
            f"/orders/{order_id}",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id


@pytest.mark.asyncio
async def test_cancel_order(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test cancelling an order."""
    order_id = str(uuid.uuid4())

    mock_order = MagicMock()
    mock_order.id = uuid.UUID(order_id)
    mock_order.user_uuid = uuid.UUID("11111111-1111-1111-1111-111111111111")
    mock_order.status = "cancelled"
    mock_order.items = []
    mock_order.subtotal = 0
    mock_order.tax = 0
    mock_order.discount = 0
    mock_order.shipping = 0
    mock_order.total = 0
    mock_order.currency = "RUB"
    mock_order.payment_method = None
    mock_order.shipping_address = None
    mock_order.notes = None
    mock_order.idempotency_key = None
    mock_order.created_at = __import__("datetime").datetime(2024, 1, 1)
    mock_order.updated_at = __import__("datetime").datetime(2024, 1, 1)

    with patch("src.routers.orders._get_order_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.cancel_order = AsyncMock(return_value=mock_order)
        mock_get_svc.return_value = mock_svc

        response = await async_client.post(
            f"/orders/{order_id}/cancel",
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_cancel_order_already_cancelled(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test cancelling an already cancelled order returns conflict."""
    order_id = str(uuid.uuid4())

    with patch("src.routers.orders._get_order_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.cancel_order = AsyncMock(
            side_effect=ValueError("Cannot cancel order in status cancelled")
        )
        mock_get_svc.return_value = mock_svc

        response = await async_client.post(
            f"/orders/{order_id}/cancel",
            headers=auth_headers,
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_unauthorized_access(
    async_client: AsyncClient,
) -> None:
    """Test accessing endpoints without auth."""
    response = await async_client.get("/orders")
    assert response.status_code == 403
