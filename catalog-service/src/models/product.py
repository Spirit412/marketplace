from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.datatype import uuid7
from src.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.category import Category


class Product(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        Index(
            "ix_products_custom_properties",
            "custom_properties_config",
            postgresql_using="gin",
        ),
        Index(
            "ix_products_search_vector",
            "search_vector",
            postgresql_using="gin",
        ),
        Index("ix_products_category_id", "category_id"),
        Index("ix_products_seller_id", "seller_id"),
        Index("ix_products_is_active", "is_active"),
        Index("ix_products_price", "price"),
        Index(
            "ix_products_numeric_properties",
            "numeric_properties",
            postgresql_using="gin",
            postgresql_ops={"numeric_properties": "jsonb_path_ops"},
        ),
        {"schema": "catalog", "comment": "Товар продавца"},
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ товара"
    )
    seller_id: Mapped[UUID] = mapped_column(
        nullable=False, index=True, comment="Продавец-владелец товара"
    )
    category_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("catalog.categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="Категория товара (fk на categories.id)",
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Название товара"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Описание товара"
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00"), comment="Цена товара"
    )
    sku: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True, comment="Артикул (SKU)"
    )
    stock: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Остаток на складе (денормализация)"
    )
    rating: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="Средний рейтинг товара"
    )

    custom_properties_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Динамические атрибуты товара (цвет, материал и т.п.)",
    )
    numeric_properties: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Числовые атрибуты для диапазонных фильтров (вес и т.п.)",
    )
    images: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Список изображений товара",
    )
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, nullable=True, comment="Полнотекстовый поисковый индекс"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Признак активности товара"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        comment="Статус товара (active/draft/archived)",
    )

    category: Mapped[Category | None] = relationship(
        back_populates="products",
        lazy="selectin",
    )
