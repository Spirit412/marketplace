import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OrderClient:
    """Client for order-service HTTP API."""

    def __init__(self, base_url: str, system_token: str, timeout: int = 15) -> None:
        self._base_url = base_url
        self._system_token = system_token
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._system_token}"}

    async def get_pending_orders(self, older_than_minutes: int) -> list[dict[str, Any]]:
        """Fetch orders in pending_payment status, created more than N minutes ago."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}/orders/pending",
                    params={"older_than_minutes": older_than_minutes},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                orders: list[dict[str, Any]] = resp.json()
            except Exception as exc:
                logger.warning("Failed to fetch pending orders: %s", exc)
                return []
            else:
                return orders

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order via order-service."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.post(
                    f"{self._base_url}/orders/{order_id}/cancel",
                    headers=self._headers(),
                )
                resp.raise_for_status()
            except Exception as exc:
                logger.warning("Failed to cancel order %s: %s", order_id, exc)
                return False
            else:
                return True
