from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted, mark_deleted
from src.models.category import Category
from src.models.property import CategoryProperty


class CategoryRepo:
    """Repository for Category; soft-deleted rows are hidden unless asked for."""

    async def get_by_id(
        self,
        session: AsyncSession,
        category_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Category | None:
        stmt = exclude_deleted(
            select(Category).where(Category.id == category_id),
            Category,
            include_deleted,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(
        self,
        session: AsyncSession,
        slug: str,
        *,
        include_deleted: bool = False,
    ) -> Category | None:
        stmt = exclude_deleted(
            select(Category).where(Category.slug == slug), Category, include_deleted
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, category: Category) -> Category:
        session.add(category)
        await session.flush()
        await session.refresh(category, attribute_names=["properties"])
        return category

    async def update(self, session: AsyncSession, category: Category) -> Category:
        """Persist changes and return the row re-read with its relations loaded.

        Re-selecting rather than returning the merged instance means the
        caller always gets eagerly-loaded relationships, so serializing the
        result never triggers lazy IO outside the async context.
        """
        merged = await session.merge(category)
        await session.flush()
        refreshed = await self.get_by_id(session, merged.id)
        return refreshed if refreshed is not None else merged

    async def delete(self, session: AsyncSession, category_id: UUID) -> bool:
        """Soft-delete a category, keeping the row for history."""
        category = await self.get_by_id(session, category_id)
        if category is None:
            return False
        mark_deleted(category)
        await session.flush()
        return True

    async def restore(self, session: AsyncSession, category_id: UUID) -> bool:
        """Clear the soft-delete flag on a category."""
        category = await self.get_by_id(session, category_id, include_deleted=True)
        if category is None:
            return False
        mark_deleted(category, False)
        await session.flush()
        return True

    async def get_tree(
        self, session: AsyncSession, *, include_deleted: bool = False
    ) -> list[Category]:
        stmt = exclude_deleted(
            select(Category).order_by(Category.tree_id, Category.lft),
            Category,
            include_deleted,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_ancestors(
        self,
        session: AsyncSession,
        category: Category,
        *,
        include_deleted: bool = False,
    ) -> list[Category]:
        stmt = exclude_deleted(
            select(Category)
            .where(
                Category.tree_id == category.tree_id,
                Category.lft < category.lft,
                Category.rgt > category.rgt,
            )
            .order_by(Category.lft),
            Category,
            include_deleted,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_descendants(
        self,
        session: AsyncSession,
        category: Category,
        *,
        include_deleted: bool = False,
    ) -> list[Category]:
        stmt = exclude_deleted(
            select(Category)
            .where(
                Category.tree_id == category.tree_id,
                Category.lft > category.lft,
                Category.rgt < category.rgt,
            )
            .order_by(Category.lft),
            Category,
            include_deleted,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def move_node(
        self,
        session: AsyncSession,
        category: Category,
        new_parent_id: UUID | None,
    ) -> Category:
        category.parent_id = new_parent_id
        await session.merge(category)
        await session.flush()
        return category

    async def get_category_properties(
        self, session: AsyncSession, category_id: UUID
    ) -> list[CategoryProperty]:
        stmt = (
            select(CategoryProperty)
            .where(CategoryProperty.category_id == category_id)
            .order_by(CategoryProperty.sort_order)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
