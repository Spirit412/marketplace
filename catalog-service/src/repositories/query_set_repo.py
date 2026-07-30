import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted, mark_deleted
from src.models.query_set import QuerySet


class QuerySetRepo:
    """Repository for QuerySet; soft-deleted rows are hidden unless asked for."""

    async def get_by_id(
        self,
        session: AsyncSession,
        query_set_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> QuerySet | None:
        stmt = exclude_deleted(
            select(QuerySet).where(QuerySet.id == query_set_id),
            QuerySet,
            include_deleted,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, query_set: QuerySet) -> QuerySet:
        session.add(query_set)
        await session.flush()
        return query_set

    async def update(self, session: AsyncSession, query_set: QuerySet) -> QuerySet:
        await session.merge(query_set)
        await session.flush()
        return query_set

    async def delete(self, session: AsyncSession, query_set_id: uuid.UUID) -> bool:
        """Soft-delete a query set, keeping the row for history."""
        qs = await self.get_by_id(session, query_set_id)
        if qs is None:
            return False
        mark_deleted(qs)
        await session.flush()
        return True

    async def restore(self, session: AsyncSession, query_set_id: uuid.UUID) -> bool:
        """Clear the soft-delete flag on a query set."""
        qs = await self.get_by_id(session, query_set_id, include_deleted=True)
        if qs is None:
            return False
        mark_deleted(qs, False)
        await session.flush()
        return True

    async def get_by_seller(
        self,
        session: AsyncSession,
        seller_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[QuerySet], int]:
        stmt = exclude_deleted(
            select(QuerySet).where(QuerySet.seller_id == seller_id), QuerySet
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await session.execute(stmt)
        query_sets = list(result.scalars().all())
        return query_sets, total

    async def get_system(self, session: AsyncSession) -> list[QuerySet]:
        stmt = exclude_deleted(
            select(QuerySet).where(QuerySet.is_system.is_(True)), QuerySet
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_favorites(
        self, session: AsyncSession, seller_id: uuid.UUID
    ) -> list[QuerySet]:
        stmt = exclude_deleted(
            select(QuerySet).where(
                QuerySet.seller_id == seller_id,
                QuerySet.is_favorite.is_(True),
            ),
            QuerySet,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def toggle_favorite(
        self, session: AsyncSession, query_set_id: uuid.UUID
    ) -> QuerySet | None:
        qs = await self.get_by_id(session, query_set_id)
        if qs is None:
            return None
        qs.is_favorite = not qs.is_favorite
        await session.merge(qs)
        await session.flush()
        return qs
