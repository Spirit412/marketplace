import logging

import httpx

logger = logging.getLogger(__name__)


class OrderClient:
    """Client for order-service HTTP API."""

    def __init__(self, base_url: str, timeout: int = 15) -> None:
        self._base_url = base_url
        self._timeout = timeout

    async def get_pending_orders(self, older_than_minutes: int) -> list[dict]:
        """Fetch orders in pending_payment status, created more than N minutes ago."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}/orders/pending",
                    params={"older_than_minutes": older_than_minutes},
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning("Failed to fetch pending orders: %s", exc)
                return []

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order via order-service."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.post(f"{self._base_url}/orders/{order_id}/cancel")
                resp.raise_for_status()
                return True
            except Exception as exc:
                logger.warning("Failed to cancel order %s: %s", order_id, exc)
                return False


class InventoryClient:
    """Client for inventory-service HTTP API."""

    def __init__(self, base_url: str, timeout: int = 15) -> None:
        self._base_url = base_url
        self._timeout = timeout

    async def get_low_stock_items(self, threshold: int) -> list[dict]:
        """Fetch items with stock below threshold."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}/inventory/low-stock",
                    params={"threshold": threshold},
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning("Failed to fetch low-stock items: %s", exc)
                return []

    async def get_popular_products(self, limit: int = 50) -> list[dict]:
        """Fetch popular products for cache warmup."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}/inventory/popular",
                    params={"limit": limit},
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning("Failed to fetch popular products: %s", exc)
                return []


class CatalogClient:
    """Client for catalog-service HTTP API."""

    def __init__(self, base_url: str, timeout: int = 15) -> None:
        self._base_url = base_url
        self._timeout = timeout

    async def get_categories(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(f"{self._base_url}/categories")
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning("Failed to fetch categories: %s", exc)
                return []


class ReportClient:
    """Client for report-service HTTP API."""

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self._base_url = base_url
        self._timeout = timeout

    async def generate_daily_report(self) -> dict | None:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.post(f"{self._base_url}/reports/daily")
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                logger.warning("Failed to generate daily report: %s", exc)
                return None
