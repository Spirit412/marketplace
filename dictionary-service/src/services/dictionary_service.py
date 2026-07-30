import logging
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy.ext.asyncio import AsyncSession

from src.engines.rabbitmq import DictionaryPublisher
from src.engines.redis import RedisDictCache
from src.enums.dictionary_type import DictionaryType
from src.models.dictionary import DictionaryEntry
from src.patterns.dictionary_registry import DictionaryRegistry
from src.repositories.dictionary_repo import DictionaryRepository

logger = logging.getLogger(__name__)


class DictionaryService:
    def __init__(
        self,
        repository: DictionaryRepository,
        redis_cache: RedisDictCache,
        publisher: DictionaryPublisher,
    ) -> None:
        self._repo = repository
        self._registry = DictionaryRegistry(repository)
        self._redis_cache = redis_cache
        self._publisher = publisher

    async def get_all(
        self,
        *,
        session: AsyncSession,
        type_: DictionaryType,
    ) -> list[dict[str, Any]]:
        cached = await self._redis_cache.get(type_.value)
        if cached:
            logger.debug("Cache hit for type %s", type_)
            return cast("list[dict[str, Any]]", cached)

        logger.debug("Cache miss for type %s, resolving from sources", type_)
        items = await self._registry.resolve(session, type_)
        if items:
            await self._redis_cache.set(type_.value, items)
        return items

    async def create_or_update(
        self,
        *,
        session: AsyncSession,
        type_: DictionaryType,
        code: str,
        data: dict[str, Any],
    ) -> DictionaryEntry:
        entry = await self._repo.upsert(session, type_, code, data)

        await self._redis_cache.invalidate(type_.value)

        payload = {
            "type": type_.value,
            "code": code,
            "action": "created" if entry.updated_at == entry.created_at else "updated",
            "changed_at": datetime.now(UTC).isoformat(),
        }
        await self._publisher.publish_dictionary_updated(payload)

        return entry

    async def delete(
        self,
        *,
        session: AsyncSession,
        type_: DictionaryType,
        code: str,
    ) -> bool:
        result = await self._repo.delete(session, type_, code)
        if result:
            await self._redis_cache.invalidate(type_.value)

            payload = {
                "type": type_.value,
                "code": code,
                "action": "deleted",
                "changed_at": datetime.now(UTC).isoformat(),
            }
            await self._publisher.publish_dictionary_updated(payload)

        return result
