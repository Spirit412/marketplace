"""Facade for order-service.

Forwards the caller's own Authorization header (see facades/catalog.py for
why) — order-service's own ownership check (an order belongs to the caller)
runs unmodified, so a customer still can't reach another customer's order
through this facade.
"""

from http import HTTPStatus
from typing import Any

import aiohttp

from src.core.http_client import CircuitBreakerClient


class OrderFacade:
    def __init__(self, base_url: str) -> None:
        self._client = CircuitBreakerClient(base_url=base_url)

    async def get_order(
        self, order_id: str, authorization: str
    ) -> dict[str, Any] | None:
        """Fetch an order by id. None if not found or not the caller's own."""
        try:
            return await self._client.get(
                f"/orders/{order_id}",
                headers={"Authorization": authorization},
            )
        except aiohttp.ClientResponseError as exc:
            if exc.status == HTTPStatus.NOT_FOUND:
                return None
            raise
