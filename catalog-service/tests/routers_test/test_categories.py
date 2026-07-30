"""Integration tests for /categories endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestCategories:
    @pytest.mark.asyncio
    async def test_create_category_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.post(
            "/categories",
            json={"name": "Test", "slug": "test"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_tree_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get("/categories")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_category_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get(
            "/categories/00000000-0000-0000-0000-000000000001",
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_update_category_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.put(
            "/categories/00000000-0000-0000-0000-000000000001",
            json={"name": "Updated"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_delete_category_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.delete(
            "/categories/00000000-0000-0000-0000-000000000001",
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_ancestors_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get(
            "/categories/00000000-0000-0000-0000-000000000001/ancestors",
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_descendants_needs_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get(
            "/categories/00000000-0000-0000-0000-000000000001/descendants",
        )
        assert response.status_code in (401, 403)
