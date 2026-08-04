from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.datatype import uuid7
from src.models.base import Base, CreatedAtMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from src.models.category import Category


class Property(CreatedAtMixin, SoftDeleteMixin, Base):
    __tablename__ = "properties"
    __table_args__ = {
        "schema": "catalog",
        "comment": "Динамическое свойство товара (цвет, размер и т.п.)",
    }

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ свойства"
    )
    backend_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Служебное имя свойства (ключ в JSONB)",
    )
    frontend_label: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Отображаемое название свойства"
    )
    property_type: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Тип значения: 0=INT,1=FLOAT,2=STR,3=LIST,4=BOOL",
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Описание свойства"
    )
    options: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Доп. настройки свойства (варианты значений и т.п.)",
    )

    category_properties: Mapped[list[CategoryProperty]] = relationship(
        back_populates="property",
    )


class CategoryProperty(Base):
    __tablename__ = "category_properties"
    __table_args__ = {
        "schema": "catalog",
        "comment": "Связь категория↔свойство (какие свойства доступны в категории)",
    }

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ связи"
    )
    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog.categories.id", ondelete="CASCADE"),
        nullable=False,
        comment="Категория (fk на categories.id)",
    )
    property_id: Mapped[UUID] = mapped_column(
        ForeignKey("catalog.properties.id", ondelete="CASCADE"),
        nullable=False,
        comment="Свойство (fk на properties.id)",
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Признак обязательности свойства в категории"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, comment="Порядок отображения свойства"
    )

    category: Mapped[Category] = relationship(
        back_populates="properties",
    )
    property: Mapped[Property] = relationship(
        back_populates="category_properties",
    )
