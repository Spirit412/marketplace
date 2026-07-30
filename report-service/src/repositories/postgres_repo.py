import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class PostgresRepository:
    """Operational queries against PostgreSQL — sellers, inventory items, etc.

    Stateless: the session is passed per call, so the repository is safe to
    register in the DI container as a single instance.
    """

    async def get_sellers(
        self, session: AsyncSession, filter_str: str | None = None
    ) -> list[dict[str, Any]]:
        return []

    async def get_inventory_items(
        self, session: AsyncSession, seller_id: uuid.UUID | None = None
    ) -> list[dict[str, Any]]:
        return []
