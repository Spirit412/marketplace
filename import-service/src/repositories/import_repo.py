import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted
from src.models.import_row import ImportRow
from src.models.import_task import ImportTask


class ImportTaskRepository:
    """Repository for ImportTask; soft-deleted rows are hidden unless asked for."""

    async def create_task(self, session: AsyncSession, task_data: dict) -> ImportTask:
        task = ImportTask(**task_data)
        session.add(task)
        await session.flush()
        return task

    async def get_task(
        self, session: AsyncSession, task_id: uuid.UUID
    ) -> ImportTask | None:
        stmt = exclude_deleted(
            select(ImportTask).where(ImportTask.id == task_id), ImportTask
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self, session: AsyncSession, task_id: uuid.UUID, status: str, **extra: object
    ) -> ImportTask | None:
        values: dict[str, object] = {"status": status, **extra}
        if status in ("completed", "failed"):
            values["completed_at"] = datetime.now(UTC)
        stmt = (
            update(ImportTask)
            .where(ImportTask.id == task_id)
            .values(**values)
            .returning(ImportTask)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_progress(
        self,
        session: AsyncSession,
        task_id: uuid.UUID,
        processed: int,
        total: int,
        errors: int,
    ) -> None:
        stmt = (
            update(ImportTask)
            .where(ImportTask.id == task_id)
            .values(
                processed_rows=processed,
                total_rows=total,
                error_rows=errors,
            )
        )
        await session.execute(stmt)

    async def list_tasks(
        self, session: AsyncSession, seller_id: uuid.UUID, limit: int, offset: int
    ) -> list[ImportTask]:
        stmt = (
            select(ImportTask)
            .where(ImportTask.seller_id == seller_id)
            .order_by(ImportTask.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


class ImportRowRepository:
    async def bulk_insert_rows(self, session: AsyncSession, rows: list[dict]) -> None:
        if rows:
            session.add_all([ImportRow(**row) for row in rows])
            await session.flush()

    async def get_rows_by_task(
        self, session: AsyncSession, task_id: uuid.UUID
    ) -> list[ImportRow]:
        stmt = (
            select(ImportRow)
            .where(ImportRow.task_id == task_id)
            .order_by(ImportRow.row_number)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_task_errors(
        self, session: AsyncSession, task_id: uuid.UUID, offset: int, limit: int
    ) -> list[ImportRow]:
        stmt = (
            select(ImportRow)
            .where(ImportRow.task_id == task_id, ImportRow.is_valid.is_(False))
            .order_by(ImportRow.row_number)
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
