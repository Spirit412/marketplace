"""Integration tests for warehouse endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from src.schemes.request.inventory import WarehouseCreateRequest

pytestmark = pytest.mark.anyio


class TestWarehouseEndpoints:
    async def test_create_warehouse_requires_auth(
        self, async_client: AsyncClient
    ) -> None:
        request = WarehouseCreateRequest(
            name="Test Warehouse",
            address="123 Test St",
            timezone="UTC",
        )
        response = await async_client.post(
            "/warehouses",
            json=request.model_dump(mode="json"),
        )
        assert response.status_code == 403

    async def test_list_warehouses_requires_auth(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/warehouses")
        assert response.status_code == 403
