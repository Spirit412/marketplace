import logging
from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.http_client import CircuitBreakerClient
from src.enums.dictionary_type import DictionaryType
from src.repositories.dictionary_repo import DictionaryRepository

logger = logging.getLogger(__name__)


class DictionarySource(ABC):
    @abstractmethod
    async def fetch(
        self, session: AsyncSession, type_: DictionaryType
    ) -> list[dict]: ...


class DBDictionarySource(DictionarySource):
    def __init__(self, repository: DictionaryRepository) -> None:
        self._repository = repository

    async def fetch(self, session: AsyncSession, type_: DictionaryType) -> list[dict]:
        entries = await self._repository.get_all_by_type(session, type_)
        return [
            {
                "id": str(e.id),
                "type": e.type,
                "code": e.code,
                "data": e.data,
                "created_at": e.created_at.isoformat(),
                "updated_at": e.updated_at.isoformat(),
            }
            for e in entries
        ]


class ExternalAPISource(DictionarySource):
    def __init__(
        self,
        http_client: CircuitBreakerClient,
        api_url: str,
    ) -> None:
        self._http_client = http_client
        self._api_url = api_url

    async def fetch(self, session: AsyncSession, type_: DictionaryType) -> list[dict]:
        if type_ != DictionaryType.currencies:
            return []
        if not self._api_url:
            logger.debug("No exchange rates API URL configured; skipping")
            return []
        try:
            data = await self._http_client.get("")
            return self._parse_exchange_rates(data)
        except Exception:
            logger.exception("Failed to fetch exchange rates from external API")
            return []

    @staticmethod
    def _parse_exchange_rates(raw: dict) -> list[dict]:
        rates = raw.get("rates", {})
        items: list[dict] = []
        for currency_code, rate in rates.items():
            items.append(
                {
                    "type": "currencies",
                    "code": currency_code,
                    "data": {"rate": rate},
                }
            )
        return items
