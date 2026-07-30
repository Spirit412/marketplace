import json
import logging
from typing import Any

import redis.asyncio as redis_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings
from src.models.notification import Template
from src.repositories.template_repo import TemplateRepository

logger = logging.getLogger(__name__)


class TemplateService:
    """Cached template lookup — Redis first, then DB, with TTL."""

    def __init__(
        self,
        template_repo: TemplateRepository,
        redis_client: redis_asyncio.Redis,
        settings: Settings,
    ) -> None:
        self._repo = template_repo
        self._redis = redis_client
        self._settings = settings

    async def find_template(
        self, session: AsyncSession, code: str, locale: str
    ) -> Template | None:
        cache_key = f"cache:template:{code}:{locale}"

        try:
            cached = await self._redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                return Template(**data)
        except Exception as exc:
            logger.debug("Redis cache miss for %s: %s", cache_key, exc)

        template = await self._repo.get_by_code_and_locale(session, code, locale)
        if template is not None:
            await self._cache_template(cache_key, template)

        return template

    async def load_all_active(self, session: AsyncSession) -> list[Template]:
        return await self._repo.get_all(session)

    async def invalidate_cache(self, code: str, locale: str) -> None:
        cache_key = f"cache:template:{code}:{locale}"
        try:
            await self._redis.delete(cache_key)
        except Exception as exc:
            logger.warning("Failed to invalidate cache key %s: %s", cache_key, exc)

    async def _cache_template(self, key: str, template: Template) -> None:
        try:
            data: dict[str, Any] = {
                "id": str(template.id),
                "code": template.code,
                "locale": template.locale,
                "subject": template.subject,
                "body_template": template.body_template,
                "channels": template.channels,
                "is_active": template.is_active,
            }
            ttl = self._settings.TEMPLATE_CACHE_TTL
            await self._redis.setex(key, ttl, json.dumps(data))
        except Exception as exc:
            logger.warning("Failed to cache template %s: %s", key, exc)
