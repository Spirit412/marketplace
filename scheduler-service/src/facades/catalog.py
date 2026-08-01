import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class CatalogClient:
    """Client for catalog-service HTTP API."""

    def __init__(self, base_url: str, system_token: str, timeout: int = 15) -> None:
        self._base_url = base_url
        self._system_token = system_token
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._system_token}"}

    async def get_categories(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}/categories/", headers=self._headers()
                )
                resp.raise_for_status()
                body: Any = resp.json()
                categories: list[dict[str, Any]] = (
                    body["items"] if isinstance(body, dict) else body
                )
            except Exception as exc:
                logger.warning("Failed to fetch categories: %s", exc)
                return []
            else:
                return categories
