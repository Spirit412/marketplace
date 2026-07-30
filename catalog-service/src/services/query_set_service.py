import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.query_set import QuerySet
from src.repositories.query_set_repo import QuerySetRepo


class QuerySetService:
    def __init__(self, query_set_repo: QuerySetRepo) -> None:
        self._repo = query_set_repo

    async def create(
        self,
        session: AsyncSession,
        seller_id: uuid.UUID,
        name: str,
        data: dict | None = None,
        displayed_fields: dict | None = None,
        tags: dict | None = None,
    ) -> QuerySet:
        query_set = QuerySet(
            seller_id=seller_id,
            name=name,
            data=data or {},
            displayed_fields=displayed_fields or {},
            tags=tags or {},
        )
        return await self._repo.create(session, query_set)

    async def get_by_id(
        self, session: AsyncSession, query_set_id: uuid.UUID
    ) -> QuerySet | None:
        return await self._repo.get_by_id(session, query_set_id)

    async def update(
        self,
        session: AsyncSession,
        query_set_id: uuid.UUID,
        **kwargs: object,
    ) -> QuerySet | None:
        qs = await self._repo.get_by_id(session, query_set_id)
        if qs is None:
            return None

        for field, value in kwargs.items():
            if value is not None and hasattr(qs, field):
                setattr(qs, field, value)

        return await self._repo.update(session, qs)

    async def delete(self, session: AsyncSession, query_set_id: uuid.UUID) -> bool:
        return await self._repo.delete(session, query_set_id)

    async def get_by_seller(
        self,
        session: AsyncSession,
        seller_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[QuerySet], int]:
        return await self._repo.get_by_seller(session, seller_id, page, page_size)

    async def get_system(self, session: AsyncSession) -> list[QuerySet]:
        return await self._repo.get_system(session)

    async def get_favorites(
        self, session: AsyncSession, seller_id: uuid.UUID
    ) -> list[QuerySet]:
        return await self._repo.get_favorites(session, seller_id)

    async def toggle_favorite(
        self, session: AsyncSession, query_set_id: uuid.UUID
    ) -> QuerySet | None:
        return await self._repo.toggle_favorite(session, query_set_id)
