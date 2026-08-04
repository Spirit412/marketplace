import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.http_client import CircuitBreakerClient
from src.enums.dictionary_type import DictionaryType
from src.repositories.dictionary_repo import DictionaryRepository
from src.services.dictionary_source import (
    DBDictionarySource,
    DictionarySource,
    ExternalAPISource,
)

logger = logging.getLogger(__name__)


class DictionaryRegistry:
    def __init__(self, repository: DictionaryRepository) -> None:
        db_source = DBDictionarySource(repository)
        self._registry: dict[DictionaryType, list[DictionarySource]] = {}

        for dict_type in DictionaryType:
            sources: list[DictionarySource] = []

            if dict_type == DictionaryType.currencies:
                if settings.EXCHANGE_RATES_API_URL:
                    http_client = CircuitBreakerClient(
                        base_url=settings.EXCHANGE_RATES_API_URL,
                    )
                    sources.append(
                        ExternalAPISource(
                            http_client=http_client,
                            api_url=settings.EXCHANGE_RATES_API_URL,
                        )
                    )

            sources.append(db_source)
            self._registry[dict_type] = sources

    async def resolve(
        self, session: AsyncSession, type_: DictionaryType
    ) -> list[dict[str, Any]]:
        sources = self._registry.get(type_, [])
        merged: dict[str, dict[str, Any]] = {}
        for source in sources:
            try:
                items = await source.fetch(session, type_)
                for item in items:
                    code = item.get("code", "")
                    if code not in merged:
                        merged[code] = item
            except Exception:
                logger.exception("Source %s failed for type %s", source, type_)
        return list(merged.values())
