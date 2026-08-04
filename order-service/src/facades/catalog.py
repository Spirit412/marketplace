from typing import Any

from src.core.http_client import CircuitBreakerClient


class CatalogClient:
    """Client for catalog-service — resolves real product name/price at order time.

    OrderBuilder.add_items() used to leave every item at price=0,
    product_name="" — nothing ever called catalog-service to fill them in.
    """

    def __init__(self, base_url: str, system_token: str) -> None:
        self._client = CircuitBreakerClient(base_url=base_url)
        self._system_token = system_token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._system_token}"}

    async def get_product(self, product_id: str) -> dict[str, Any]:
        """Fetch a single product's current name/price/seller_id."""
        return await self._client.get(
            f"/products/{product_id}", headers=self._headers()
        )
