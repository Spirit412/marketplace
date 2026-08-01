"""Facade for catalog-service.

Every method forwards the caller's own Authorization header, never a
system/service token — catalog-service's own RBAC check runs exactly as it
would for a direct browser request. See PLAN_api-service.md for why this
matters (a system token would bypass per-resource ownership checks).
"""

from http import HTTPStatus
from typing import Any

import aiohttp

from src.core.http_client import CircuitBreakerClient


class CatalogFacade:
    def __init__(self, base_url: str) -> None:
        self._client = CircuitBreakerClient(base_url=base_url)

    async def get_product(
        self, product_id: str, authorization: str
    ) -> dict[str, Any] | None:
        """Fetch a product by id. None if catalog-service returns 404."""
        try:
            return await self._client.get(
                f"/products/{product_id}",
                headers={"Authorization": authorization},
            )
        except aiohttp.ClientResponseError as exc:
            if exc.status == HTTPStatus.NOT_FOUND:
                return None
            raise
