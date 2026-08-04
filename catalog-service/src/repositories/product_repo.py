from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import exclude_deleted, mark_deleted
from src.models.product import Product
from src.services.query_constructor import ProductQueryConstructor
from src.services.sort_strategy import get_sort_strategy


class ProductRepo:
    """Repository for Product; soft-deleted rows are hidden unless asked for."""

    async def get_by_id(
        self,
        session: AsyncSession,
        product_id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Product | None:
        stmt = exclude_deleted(
            select(Product).where(Product.id == product_id), Product, include_deleted
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(
        self, session: AsyncSession, sku: str, *, include_deleted: bool = False
    ) -> Product | None:
        stmt = exclude_deleted(
            select(Product).where(Product.sku == sku), Product, include_deleted
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, product: Product) -> Product:
        session.add(product)
        await session.flush()
        return product

    async def update(self, session: AsyncSession, product: Product) -> Product:
        await session.merge(product)
        await session.flush()
        # updated_at is server-side (onupdate=func.now()) — flush() alone
        # leaves it expired on the Python object; the next (synchronous)
        # attribute read, e.g. Pydantic serializing the response, would need
        # to lazy-load it and fail with MissingGreenlet outside an await.
        await session.refresh(product)
        return product

    async def delete(self, session: AsyncSession, product_id: UUID) -> bool:
        """Soft-delete a product, keeping the row for history."""
        product = await self.get_by_id(session, product_id)
        if product is None:
            return False
        mark_deleted(product)
        await session.flush()
        return True

    async def restore(self, session: AsyncSession, product_id: UUID) -> bool:
        """Clear the soft-delete flag on a product."""
        product = await self.get_by_id(session, product_id, include_deleted=True)
        if product is None:
            return False
        mark_deleted(product, False)
        await session.flush()
        return True

    def base_query(self, *, include_deleted: bool = False) -> Select[Any]:
        return exclude_deleted(
            select(Product).where(Product.is_active.is_(True)), Product, include_deleted
        )

    async def search(  # noqa: PLR0913 -- one filter dimension per param, all optional
        self,
        session: AsyncSession,
        *,
        query: str | None = None,
        category_id: UUID | None = None,
        seller_id: UUID | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        status: str | None = None,
        filters: dict[str, str] | None = None,
        sort: str = "newest",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        stmt = self.base_query()

        if query:
            stmt = ProductQueryConstructor.apply_search(stmt, query)
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        if seller_id:
            stmt = stmt.where(Product.seller_id == seller_id)
        if price_min is not None:
            stmt = stmt.where(Product.price >= price_min)
        if price_max is not None:
            stmt = stmt.where(Product.price <= price_max)
        if status:
            stmt = stmt.where(Product.status == status)
        if filters:
            stmt = ProductQueryConstructor.apply_filters(stmt, filters)

        stmt = get_sort_strategy(sort).apply(stmt)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await session.execute(stmt)
        products = list(result.scalars().all())

        return products, total
