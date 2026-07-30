from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import and_, func, or_, select
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
        stmt = select(func.count(Permission.uuid))
        if search_value:
            stmt = stmt.where(
                or_(
                    Permission.name.ilike(f"%{search_value}%"),
                    Permission.app_id.ilike(f"%{search_value}%"),
                )
            )
        result = await session.execute(stmt)
        return result.scalar_one() or 0

    async def check_by_uuids(
        self, session: AsyncSession, uuids: set[UUID]
    ) -> list[Permission]:
        stmt = select(Permission).where(Permission.uuid.in_(uuids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def check_additional_access(
        self,
        session: AsyncSession,
        *,
        path: str,
        method: str,
        app_id: str,
        additional_uuids: list[UUID],
    ) -> bool:
        """Check if any of the additional permission UUIDs grant access."""
        if not additional_uuids:
            return False
        stmt = select(Permission.uuid).where(
            and_(
                Permission.uuid.in_(additional_uuids),
                Permission.app_id == app_id,
                Permission.method == method,
                Permission.path == "/*",
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None
