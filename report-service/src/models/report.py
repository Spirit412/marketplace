from datetime import datetime
from typing import Any
from uuid import UUID as PyUUID

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.datatype import uuid7
from src.models.base import Base, SoftDeleteMixin, TimestampMixin


class Report(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "reports"
    __table_args__ = {
        "schema": "report",
        "comment": "Сформированный или формируемый отчёт",
    }

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
        comment="Первичный ключ отчёта",
    )
    user_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, comment="Пользователь, запросивший отчёт"
    )
    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Тип отчёта (sales/inventory/customers/products)",
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Параметры формирования отчёта (фильтры, период)",
    )
    format: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="csv",
        comment="Формат экспорта (csv/xlsx/pdf)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        comment="Статус формирования отчёта",
    )
    file_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Путь к сгенерированному файлу в хранилище"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Сообщение об ошибке формирования"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата завершения формирования отчёта",
    )


class ReportTemplate(SoftDeleteMixin, Base):
    __tablename__ = "report_templates"
    __table_args__ = {
        "schema": "report",
        "comment": "Шаблон отчёта (SQL-запрос и схема параметров)",
    }

    id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
        comment="Первичный ключ шаблона",
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True, comment="Название шаблона отчёта"
    )
    sql_template: Mapped[str] = mapped_column(
        Text, nullable=False, comment="SQL-запрос шаблона"
    )
    parameters_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Схема допустимых параметров отчёта",
    )
