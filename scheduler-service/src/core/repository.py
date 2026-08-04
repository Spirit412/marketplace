import math
from collections.abc import Sequence
from typing import Any, cast

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.orm import Base, SoftDeleteMixin


def supports_soft_delete(model: type) -> bool:
    """Whether a model carries SoftDeleteMixin."""
    return isinstance(model, type) and issubclass(model, SoftDeleteMixin)


def exclude_deleted[S: Select[Any]](
    stmt: S, model: type, include_deleted: bool = False
) -> S:
    """Filter soft-deleted rows out of a statement.

    A no-op when the model has no soft-delete support or when deleted rows were
    explicitly requested, so repositories can apply it unconditionally.

    Args:
        stmt: The select being built.
        model: The mapped class the statement selects from.
        include_deleted: Skip the filter and return flagged rows too.

    Returns:
        The statement, narrowed to live rows where applicable.
    """
    if include_deleted or not supports_soft_delete(model):
        return stmt
    return stmt.where(cast("type[SoftDeleteMixin]", model).is_delete.is_(False))


def mark_deleted(instance: object, deleted: bool = True) -> None:
    """Set or clear an instance's soft-delete flag.

    Args:
        instance: A mapped instance whose class carries SoftDeleteMixin.
        deleted: Value to write to the flag.

    Raises:
        NotImplementedError: If the instance's model has no soft-delete support.
    """
    if not supports_soft_delete(type(instance)):
        msg = f"{type(instance).__name__} does not support soft delete"
        raise NotImplementedError(msg)
    cast("SoftDeleteMixin", instance).is_delete = deleted


class BaseRepository[T: Base]:
    """Generic async repository for CRUD operations on SQLAlchemy models.

    Read methods and `delete()` are soft-delete aware: when the model carries
    `SoftDeleteMixin`, rows flagged `is_delete` are hidden from reads and
    `delete()` sets the flag instead of issuing a DELETE. Models without the
    mixin (append-only audit logs, association tables) keep hard-delete
    semantics. Pass `include_deleted=True` to read flagged rows.

    Type Parameters:
        T: SQLAlchemy DeclarativeBase model class.
    """

    def __init__(self, model: type[T]) -> None:
        self._model = model

    @property
    def model(self) -> type[T]:
        return self._model

    @property
    def supports_soft_delete(self) -> bool:
        """Whether this repository's model carries SoftDeleteMixin."""
        return issubclass(self._model, SoftDeleteMixin)

    @property
    def _soft_delete_column(self) -> Any:
        """The model's is_delete column; only valid when soft delete is supported."""
        return cast("type[SoftDeleteMixin]", self._model).is_delete

    def _apply_soft_delete_filter(
        self, stmt: Select[tuple[T]], include_deleted: bool
    ) -> Select[tuple[T]]:
        """Hide soft-deleted rows unless explicitly asked for."""
        if include_deleted or not self.supports_soft_delete:
            return stmt
        return stmt.where(self._soft_delete_column.is_(False))

    async def get_by(
        self,
        session: AsyncSession,
        *,
        include_deleted: bool = False,
        **filters: Any,
    ) -> T | None:
        stmt = select(self._model).filter_by(**filters)
        stmt = self._apply_soft_delete_filter(stmt, include_deleted)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        session: AsyncSession,
        entity_id: Any,
        *,
        include_deleted: bool = False,
    ) -> T | None:
        stmt = select(self._model).where(self._model.id == entity_id)  # type: ignore[attr-defined]
        stmt = self._apply_soft_delete_filter(stmt, include_deleted)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, session: AsyncSession, instance: T) -> T:
        session.add(instance)
        await session.flush()
        return instance

    async def commit(self, session: AsyncSession) -> None:
        """Force the current transaction durable now, ahead of the request's own commit.

        get_async_session()'s own commit only runs once the request unwinds
        all the way back up through the router. A caller that's about to
        raise (aborting the request, which would otherwise roll back)
        needs this to make already-applied writes durable first, instead of
        losing them to that rollback.
        """
        await session.commit()

    async def update(self, session: AsyncSession, instance: T, **values: Any) -> T:
        for key, value in values.items():
            setattr(instance, key, value)
        await session.flush()
        return instance

    async def delete(self, session: AsyncSession, instance: T) -> T:
        """Soft-delete when supported, otherwise remove the row."""
        if self.supports_soft_delete:
            cast("SoftDeleteMixin", instance).is_delete = True
        else:
            await session.delete(instance)
        await session.flush()
        return instance

    async def restore(self, session: AsyncSession, instance: T) -> T:
        """Clear the soft-delete flag.

        Raises:
            NotImplementedError: If the model has no soft-delete support.
        """
        if not self.supports_soft_delete:
            msg = f"{self._model.__name__} does not support soft delete"
            raise NotImplementedError(msg)
        cast("SoftDeleteMixin", instance).is_delete = False
        await session.flush()
        return instance

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Any = None,
        include_deleted: bool = False,
        **filters: Any,
    ) -> Sequence[T]:
        stmt = select(self._model).filter_by(**filters)
        stmt = self._apply_soft_delete_filter(stmt, include_deleted)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def count(
        self, session: AsyncSession, *, include_deleted: bool = False, **filters: Any
    ) -> int:
        stmt = select(func.count()).select_from(self._model).filter_by(**filters)
        if not include_deleted and self.supports_soft_delete:
            stmt = stmt.where(self._soft_delete_column.is_(False))
        result = await session.execute(stmt)
        return result.scalar_one()

    async def _paginate_stmt(
        self,
        session: AsyncSession,
        *,
        stmt: Select[tuple[T]],
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[T], int, int]:
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await session.execute(count_stmt)
        total_items: int = total_result.scalar_one()
        total_pages = max(1, math.ceil(total_items / page_size))

        offset_count = (page - 1) * page_size
        paginated_stmt = stmt.offset(offset_count).limit(page_size)
        result = await session.execute(paginated_stmt)

        return list(result.scalars().all()), total_pages, total_items

    def base_query(self, *, include_deleted: bool = False) -> Select[tuple[T]]:
        """Start a query with the soft-delete filter already applied."""
        return self._apply_soft_delete_filter(select(self._model), include_deleted)
