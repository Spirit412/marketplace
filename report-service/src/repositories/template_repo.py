from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted
from src.models.report import ReportTemplate


class ReportTemplateRepo:
    """Repository for ReportTemplate; soft-deleted rows are hidden unless asked for.

    Stateless: the session is passed per call, so the repository is safe to
    register in the DI container as a single instance.
    """

    async def get_by_id(
        self,
        session: AsyncSession,
        template_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> ReportTemplate | None:
        stmt = exclude_deleted(
            select(ReportTemplate).where(ReportTemplate.id == template_id),
            ReportTemplate,
            include_deleted,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(
        self, session: AsyncSession, name: str, *, include_deleted: bool = False
    ) -> ReportTemplate | None:
        stmt = exclude_deleted(
            select(ReportTemplate).where(ReportTemplate.name == name),
            ReportTemplate,
            include_deleted,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self, session: AsyncSession, *, include_deleted: bool = False
    ) -> list[ReportTemplate]:
        stmt = exclude_deleted(
            select(ReportTemplate).order_by(ReportTemplate.name),
            ReportTemplate,
            include_deleted,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
