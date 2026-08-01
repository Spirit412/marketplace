from typing import Any

import httpx

from src.config.settings import settings


class DictionaryClient:
    def __init__(self) -> None:
        self._base_url = settings.DICTIONARY_SERVICE_URL
        self._token = settings.SYSTEM_TOKEN

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def get_units(self) -> dict[str, Any]:
        """Fetch the units dictionary — used as a lightweight connectivity probe."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self._base_url}/dictionaries/units",
                headers=self._headers(),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
