import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class InventoryClient:
    """Client for inventory-service HTTP API."""

    def __init__(self, base_url: str, system_token: str, timeout: int = 15) -> None:
        self._base_url = base_url
        self._system_token = system_token
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._system_token}"}

    async def get_low_stock_items(self, threshold: int) -> list[dict[str, Any]]:
        """Fetch items with stock below threshold."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}/stock/low-stock",
                    params={"threshold": threshold},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                items: list[dict[str, Any]] = resp.json()
            except Exception as exc:
                logger.warning("Failed to fetch low-stock items: %s", exc)
                return []
            else:
                return items

    async def get_popular_products(self, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch popular products for cache warmup."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}/stock/popular",
                    params={"limit": limit},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                products: list[dict[str, Any]] = resp.json()
            except Exception as exc:
                logger.warning("Failed to fetch popular products: %s", exc)
                return []
            else:
                return products
