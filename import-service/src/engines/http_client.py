import httpx

from src.config.settings import settings


class CatalogClient:
    def __init__(self) -> None:
        self._base_url = settings.CATALOG_SERVICE_URL
        self._token = settings.SYSTEM_TOKEN

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def create_products(self, products: list[dict]) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
        f"{self._base_url}/products/bulk",
        json={"products": products},
        headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()


class DictionaryClient:
    def __init__(self) -> None:
        self._base_url = settings.DICTIONARY_SERVICE_URL
        self._token = settings.SYSTEM_TOKEN

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def get_categories(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
        f"{self._base_url}/categories",
        headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_brands(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
        f"{self._base_url}/brands",
        headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_units(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
        f"{self._base_url}/units",
        headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()
