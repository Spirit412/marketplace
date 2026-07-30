import logging

from src.models.notification import Template

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """In-memory registry of notification templates, keyed by code (event_type)."""

    def __init__(self) -> None:
        self._registry: dict[str, Template] = {}

    async def load(self, templates: list[Template]) -> None:
        """Load (or reload) templates from the database."""
        self._registry.clear()
        for tpl in templates:
            self._registry[tpl.code] = tpl
        logger.info("TemplateRegistry loaded %d templates", len(self._registry))

    def get(self, event_type: str, locale: str = "ru") -> Template | None:
        """Look up template by event_type code. Falls back to any locale."""
        tpl = self._registry.get(event_type)
        if tpl is not None:
            return tpl

        for key, tpl in self._registry.items():
            if key == event_type:
                return tpl
        return None

    def invalidate(self) -> None:
        self._registry.clear()

    def __contains__(self, event_type: str) -> bool:
        return event_type in self._registry

    def __len__(self) -> int:
        return len(self._registry)
