"""Facade for inventory-service.

Forwards the caller's own Authorization header (see facades/catalog.py for
why).
"""

from http import HTTPStatus
from typing import Any

import aiohttp

from src.core.http_client import CircuitBreakerClient


class InventoryFacade:
    def __init__(self, base_url: str) -> None:
        self._client = CircuitBreakerClient(base_url=base_url)

    async def check_stock_by_product(
        self, product_id: str, authorization: str, quantity: int = 1
    ) -> dict[str, Any] | None:
        """Find a warehouse with at least `quantity` of this product.

        inventory-service's GET /stock/by-product/{id} answers "is a
        quantity available", not "what's the total count" — it 404s if no
        single warehouse can satisfy `quantity`. Defaulting to 1 turns it
        into a plain in-stock check for the storefront card; callers that
        need "can I buy N" pass their own quantity.
        """
        try:
            return await self._client.get(
                f"/stock/by-product/{product_id}",
                params={"quantity": quantity},
                headers={"Authorization": authorization},
            )
        except aiohttp.ClientResponseError as exc:
            if exc.status == HTTPStatus.NOT_FOUND:
                return None
            raise
