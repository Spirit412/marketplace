"""Integration tests for cart endpoints."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_add_to_cart(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test adding an item to cart."""
    product_id = str(uuid.uuid4())

    with patch("src.routers.cart._get_cart_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.add_item = AsyncMock(
            return_value={product_id: 2}
        )
        mock_get_svc.return_value = mock_svc

        response = await async_client.post(
            "/cart",
            json={"product_id": product_id, "quantity": 2},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == product_id
    assert data["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_get_cart_empty(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test getting an empty cart."""
    with patch("src.routers.cart._get_cart_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.get_cart = AsyncMock(return_value={})
        mock_get_svc.return_value = mock_svc

        response = await async_client.get(
            "/cart", headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []


@pytest.mark.asyncio
async def test_get_cart_with_items(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test getting a cart with items."""
    product_id = str(uuid.uuid4())

    with patch("src.routers.cart._get_cart_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.get_cart = AsyncMock(
            return_value={product_id: 3}
        )
        mock_get_svc.return_value = mock_svc

        response = await async_client.get(
            "/cart", headers=auth_headers
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == product_id
    assert data["items"][0]["quantity"] == 3


@pytest.mark.asyncio
async def test_remove_from_cart(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test removing an item from cart."""
    product_id = str(uuid.uuid4())

    with patch("src.routers.cart._get_cart_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.remove_item = AsyncMock()
        mock_get_svc.return_value = mock_svc

        response = await async_client.delete(
            f"/cart/{product_id}",
            headers=auth_headers,
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_clear_cart(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test clearing the entire cart."""
    with patch("src.routers.cart._get_cart_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.clear_cart = AsyncMock()
        mock_get_svc.return_value = mock_svc

        response = await async_client.delete(
            "/cart", headers=auth_headers
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_unauthorized_access(
    async_client: AsyncClient,
) -> None:
    """Test accessing cart endpoints without auth."""
    response = await async_client.get("/cart")
    assert response.status_code == 403

    response = await async_client.post(
        "/cart",
        json={
            "product_id": str(uuid.uuid4()),
            "quantity": 1,
        },
    )
    assert response.status_code == 403
