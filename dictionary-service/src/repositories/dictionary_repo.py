from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted, mark_deleted
from src.enums.dictionary_type import DictionaryType
from src.models.dictionary import DictionaryEntry


class DictionaryRepository:
    """Repository for DictionaryEntry; soft-deleted rows are hidden unless asked for.

    Stateless: the session is passed per call, so the repository is safe to
    register in the DI container as a single instance.
    """

    async def get_all_by_type(
        self,
        session: AsyncSession,
        type_: DictionaryType,
        *,
        include_deleted: bool = False,
    ) -> list[DictionaryEntry]:
        stmt = exclude_deleted(
            select(DictionaryEntry).where(DictionaryEntry.type == type_),
            DictionaryEntry,
            include_deleted,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type_and_code(
        self,
        session: AsyncSession,
        type_: DictionaryType,
        code: str,
        *,
        include_deleted: bool = False,
    ) -> DictionaryEntry | None:
        stmt = exclude_deleted(
            select(DictionaryEntry).where(
                DictionaryEntry.type == type_,
                DictionaryEntry.code == code,
            ),
            DictionaryEntry,
            include_deleted,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self,
        session: AsyncSession,
        type_: DictionaryType,
        code: str,
        data: dict[str, Any],
    ) -> DictionaryEntry:
        stmt = (
            insert(DictionaryEntry)
            .values(type=type_.value, code=code, data=data)
            .on_conflict_do_update(
                index_elements=["type", "code"],
                set_={"data": data},
            )
            .returning(DictionaryEntry)
        )
        result = await session.execute(stmt)
        await session.flush()
        entry = result.scalar_one()
        await session.refresh(entry)
        return entry

    async def delete(
        self, session: AsyncSession, type_: DictionaryType, code: str
    ) -> bool:
        """Soft-delete an entry, keeping the row for history."""
        entry = await self.get_by_type_and_code(session, type_, code)
        if entry is None:
            return False
        mark_deleted(entry)
        await session.flush()
        return True
