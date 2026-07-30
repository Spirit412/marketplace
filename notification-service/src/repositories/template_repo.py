import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted, mark_deleted
from src.models.notification import Template


class TemplateRepository:
    """Repository for Template; soft-deleted rows are hidden unless asked for."""


    async def get_by_code_and_locale(self, session: AsyncSession, code: str, locale: str) -> Template | None:
        stmt = exclude_deleted(
            select(Template).where(
                Template.code == code,
                Template.locale == locale,
                Template.is_active.is_(True),
            ),
            Template,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession, locale: str | None = None) -> list[Template]:
        stmt = exclude_deleted(
            select(Template).where(Template.is_active.is_(True)), Template
        )
        if locale:
            stmt = stmt.where(Template.locale == locale)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, template: Template) -> Template:
        session.add(template)
        await session.flush()
        return template

    async def update(self, session: AsyncSession, template: Template) -> Template:
        await session.merge(template)
        await session.flush()
        return template

    async def delete(self, session: AsyncSession, template_id: uuid.UUID) -> None:
        """Soft-delete a template, keeping the row for history."""
        stmt = exclude_deleted(
            select(Template).where(Template.id == template_id), Template
        )
        result = await session.execute(stmt)
        tpl = result.scalar_one_or_none()
        if tpl is not None:
            mark_deleted(tpl)
            await session.flush()
