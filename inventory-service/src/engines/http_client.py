from typing import Any

import httpx

from src.config.settings import settings


class CatalogClient:
    def __init__(self) -> None:
        self._base_url = settings.CATALOG_SERVICE_URL
        self._system_token = settings.SYSTEM_TOKEN
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self._client

    async def get_product(self, product_id: str) -> dict[str, Any] | None:
        client = await self._get_client()
        headers = {"Authorization": f"Bearer {self._system_token}"}
        response = await client.get(
            f"{self._base_url}/internal/products/{product_id}",
            headers=headers,
        )
        if response.status_code == 200:
            product: dict[str, Any] = response.json()
            return product
        return None

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


_catalog_client: CatalogClient | None = None


def get_catalog_client() -> CatalogClient:
    global _catalog_client
    if _catalog_client is None:
        _catalog_client = CatalogClient()
    return _catalog_client
