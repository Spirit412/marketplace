from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.datatype import uuid7
from src.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.product import Product
    from src.models.property import CategoryProperty


class Category(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "categories"
    __table_args__ = {
        "schema": "catalog",
        "comment": "Категория товара (дерево, MPTT: lft/rgt/tree_id)",
    }

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ категории"
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Название категории"
    )
    slug: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, comment="URL-слаг категории"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Описание категории"
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog.categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="Родительская категория (fk на categories.id)",
    )

    lft: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="MPTT: левая граница узла"
    )
    rgt: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="MPTT: правая граница узла"
    )
    tree_id: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="MPTT: идентификатор дерева"
    )
    level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Глубина вложенности категории"
    )

    parent: Mapped[Category | None] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
        lazy="selectin",
    )
    children: Mapped[list[Category]] = relationship(
        "Category",
        back_populates="parent",
        lazy="selectin",
    )
    properties: Mapped[list[CategoryProperty]] = relationship(
        back_populates="category",
        lazy="selectin",
    )
    products: Mapped[list[Product]] = relationship(
        back_populates="category",
        lazy="selectin",
    )
