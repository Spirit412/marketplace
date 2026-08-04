from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import BaseRepository
from src.models.permission import Permission


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self) -> None:
        super().__init__(Permission)

    async def search(
        self,
        session: AsyncSession,
        *,
        page: int = 1,
        page_size: int = 20,
        search_value: str | None = None,
    ) -> tuple[Sequence[Permission], int, int]:
        stmt = select(Permission)

        if search_value:
            stmt = stmt.where(
                or_(
                    Permission.name.ilike(f"%{search_value}%"),
                    Permission.app_id.ilike(f"%{search_value}%"),
                )
            )

        return await self._paginate_stmt(
            session=session,
            stmt=stmt,
            page=page,
            page_size=page_size,
        )

    async def search_count_only(
        self, session: AsyncSession, search_value: str | None = None
    ) -> int:
        stmt = select(func.count(Permission.id))
        if search_value:
            stmt = stmt.where(
                or_(
                    Permission.name.ilike(f"%{search_value}%"),
                    Permission.app_id.ilike(f"%{search_value}%"),
                )
            )
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    async def check_by_ids(
        self, session: AsyncSession, ids: set[UUID]
    ) -> list[Permission]:
        stmt = select(Permission).where(Permission.id.in_(ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())
