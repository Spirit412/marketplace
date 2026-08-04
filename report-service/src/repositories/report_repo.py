from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted
from src.models.report import Report


class ReportRepo:
    """Repository for Report; soft-deleted rows are hidden unless asked for.

    Stateless: the session is passed per call, so the repository is safe to
    register in the DI container as a single instance.
    """

    async def create(self, session: AsyncSession, report: Report) -> Report:
        session.add(report)
        await session.flush()
        return report

    async def get_by_id(
        self,
        session: AsyncSession,
        report_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Report | None:
        stmt = exclude_deleted(
            select(Report).where(Report.id == report_id), Report, include_deleted
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Report], int]:
        stmt = exclude_deleted(
            select(Report)
            .where(Report.user_id == user_id)
            .order_by(Report.created_at.desc())
            .offset(offset)
            .limit(limit),
            Report,
        )
        result = await session.execute(stmt)
        reports = list(result.scalars().all())

        count_stmt = exclude_deleted(
            select(Report).where(Report.user_id == user_id), Report
        )
        count_result = await session.execute(count_stmt)
        total = len(list(count_result.scalars().all()))

        return reports, total

    async def update_status(
        self,
        session: AsyncSession,
        report_id: UUID,
        status: str,
        file_path: str | None = None,
        error_message: str | None = None,
    ) -> Report | None:
        values: dict[str, Any] = {"status": status, "updated_at": datetime.now(UTC)}
        if file_path is not None:
            values["file_path"] = file_path
        if error_message is not None:
            values["error_message"] = error_message
        if status == "completed":
            values["completed_at"] = datetime.now(UTC)

        stmt = (
            update(Report)
            .where(Report.id == report_id)
            .values(**values)
            .returning(Report)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
