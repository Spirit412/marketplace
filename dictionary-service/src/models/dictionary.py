from src.models.base import Base, SoftDeleteMixin, TimestampMixin

import uuid

from sqlalchemy import JSON, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.datatype import uuid7



class DictionaryEntry(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "dictionary_entries"
    __table_args__ = (
        Index("ix_dictionary_entries_type_code", "type", "code", unique=True),
        {"schema": "dictionary", "comment": "Запись справочника (валюты, единицы измерения, страны и т.п.)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7, comment="Первичный ключ записи")
    type: Mapped[str] = mapped_column(String(50), index=True, nullable=False, comment="Тип справочника (currencies, units, countries...)")
    code: Mapped[str] = mapped_column(String(255), nullable=False, comment="Код записи в рамках типа справочника")
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, comment="Данные записи (JSON, формат зависит от типа)")
