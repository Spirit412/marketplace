import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted
from src.models.property import CategoryProperty, Property


class PropertyRepo:
    """Repository for Property; soft-deleted rows are hidden unless asked for."""

    async def get_by_id(
        self,
        session: AsyncSession,
        property_id: uuid.UUID,
        *,
        include_deleted: bool = False,
    ) -> Property | None:
        stmt = exclude_deleted(
            select(Property).where(Property.id == property_id), Property, include_deleted
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_backend_name(
        self, session: AsyncSession, name: str, *, include_deleted: bool = False
    ) -> Property | None:
        stmt = exclude_deleted(
            select(Property).where(Property.backend_name == name),
            Property,
            include_deleted,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, prop: Property) -> Property:
        session.add(prop)
        await session.flush()
        return prop

    async def update(self, session: AsyncSession, prop: Property) -> Property:
        await session.merge(prop)
        await session.flush()
        return prop

    async def link_category_property(
        self,
        session: AsyncSession,
        category_id: uuid.UUID,
        property_id: uuid.UUID,
        is_required: bool = False,
        sort_order: int = 0,
    ) -> CategoryProperty:
        link = CategoryProperty(
            category_id=category_id,
            property_id=property_id,
            is_required=is_required,
            sort_order=sort_order,
        )
        session.add(link)
        await session.flush()
        return link

    async def get_all(
        self, session: AsyncSession, *, include_deleted: bool = False
    ) -> list[Property]:
        stmt = exclude_deleted(
            select(Property).order_by(Property.frontend_label), Property, include_deleted
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
