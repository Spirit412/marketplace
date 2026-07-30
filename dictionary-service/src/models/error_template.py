import uuid

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.datatype import uuid7
from src.models.base import SoftDeleteMixin, TimestampMixin
from src.models.dictionary import Base


class ErrorTemplate(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "error_templates"
    __table_args__ = (
        Index("ix_error_templates_code_locale", "code", "locale", unique=True),
        {
            "schema": "dictionary",
            "comment": "Локализованный шаблон текста ошибки (используется, например, import-service)",
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ шаблона"
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False, comment="Код ошибки")
    locale: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="Локаль текста (ru, en...)"
    )
    message: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Текст сообщения с плейсхолдерами"
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="info",
        comment="Уровень серьёзности (info/warning/error)",
    )
