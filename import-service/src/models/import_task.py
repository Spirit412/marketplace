import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.datatype import uuid7
from src.models.base import Base, CreatedAtMixin, SoftDeleteMixin


class ImportTask(CreatedAtMixin, SoftDeleteMixin, Base):
    __tablename__ = "import_tasks"
    __table_args__ = {
        "schema": "import_service",
        "comment": "Задача импорта товаров/остатков продавца из CSV",
    }

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
        comment="Первичный ключ задачи",
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        index=True,
        nullable=False,
        comment="Продавец, инициировавший импорт",
    )
    import_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Тип импорта (товары, остатки, прайс-лист)"
    )
    file_name: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Исходное имя загруженного файла"
    )
    file_path: Mapped[str] = mapped_column(
        String(1000), nullable=False, comment="Путь к файлу в хранилище"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", comment="Статус задачи импорта"
    )
    total_rows: Mapped[int] = mapped_column(
        Integer, default=0, comment="Всего строк в файле"
    )
    processed_rows: Mapped[int] = mapped_column(
        Integer, default=0, comment="Обработано строк"
    )
    error_rows: Mapped[int] = mapped_column(
        Integer, default=0, comment="Строк с ошибками"
    )
    error_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="Детали ошибок импорта"
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата завершения импорта"
    )
