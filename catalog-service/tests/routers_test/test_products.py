"""Integration tests for /products endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestProducts:
    @pytest.mark.asyncio
    async def test_create_product_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.post(
            "/products",
            json={"name": "Test", "price": 10.0},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_product_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get(
            "/products/00000000-0000-0000-0000-000000000001",
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_products_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get("/products")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_update_product_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.put(
            "/products/00000000-0000-0000-0000-000000000001",
            json={"name": "Updated"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_delete_product_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.delete(
            "/products/00000000-0000-0000-0000-000000000001",
        )
        assert response.status_code in (401, 403)
