from typing import Any

import aiohttp

from src.core.http_client import CircuitBreakerClient


class InsufficientStockError(Exception):
    """No warehouse has enough stock to satisfy the requested quantity."""


class InventoryClient:
    """Client for inventory-service with circuit breaker and system auth.

    Order-service tracks products and quantities, not warehouses — every
    call here goes through inventory-service's *-by-product endpoints, which
    pick a warehouse internally and report back which one they used.
    """

    def __init__(self, base_url: str, system_token: str) -> None:
        self._base_url = base_url
        self._system_token = system_token
        self._client = CircuitBreakerClient(base_url=base_url)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._system_token}"}

    async def check_stock(self, product_uuid: str, quantity: int) -> bool:
        """Check whether any warehouse has enough stock for this product."""
        try:
            await self._client.get(
                f"/stock/by-product/{product_uuid}",
                params={"quantity": quantity},
                headers=self._headers(),
            )
            return True
        except aiohttp.ClientResponseError as exc:
            if exc.status == 404:
                return False
            raise

    async def reserve(
        self,
        product_uuid: str,
        quantity: int,
        *,
        reference_id: str | None = None,
    ) -> dict[str, Any]:
        """Reserve stock for a product, letting inventory-service pick the warehouse.

        Returns the reservation result, including `warehouse_id` — callers
        must keep it so a later release() targets the same warehouse.

        Raises:
            InsufficientStockError: no warehouse could satisfy the quantity.
        """
        try:
            return await self._client.post(
                "/stock/reserve-by-product",
                json={
                    "product_id": product_uuid,
                    "quantity": quantity,
                    "reference_type": "order",
                    "reference_id": reference_id,
                },
                headers=self._headers(),
            )
        except aiohttp.ClientResponseError as exc:
            if exc.status == 409:
                raise InsufficientStockError(
                    f"Insufficient stock for product {product_uuid}"
                ) from exc
            raise

    async def release(
        self,
        product_uuid: str,
        warehouse_id: str,
        quantity: int,
        *,
        reference_id: str | None = None,
    ) -> dict[str, Any]:
        """Release previously reserved stock from the warehouse it was reserved from."""
        return await self._client.post(
            "/stock/release",
            json={
                "product_id": product_uuid,
                "warehouse_id": warehouse_id,
                "quantity": quantity,
                "reference_type": "order",
                "reference_id": reference_id,
            },
            headers=self._headers(),
        )
