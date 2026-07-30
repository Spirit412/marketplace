import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.datatype import uuid7
from src.models.base import Base, SoftDeleteMixin, TimestampMixin


class QuerySet(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "query_sets"
    __table_args__ = {"schema": "catalog", "comment": "Сохранённый набор фильтров и отображаемых полей для товаров"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7, comment="Первичный ключ набора")
    seller_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True, comment="Продавец-владелец набора")
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="Название набора фильтров")
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, comment="Структура условий фильтрации (JSONB)")
    displayed_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, comment="Список отображаемых полей")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, comment="Признак избранного набора")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, comment="Системный набор (нельзя редактировать/удалять)")
    tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, comment="Произвольные теги набора")

