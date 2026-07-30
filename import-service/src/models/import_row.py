import uuid

from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.datatype import uuid7
from src.models.import_task import Base


class ImportRow(Base):
    __tablename__ = "import_rows"
    __table_args__ = {
        "schema": "import_service",
        "comment": "Строка исходного CSV-файла и результат её валидации",
    }

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
        comment="Первичный ключ строки",
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_service.import_tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="Задача импорта (fk на import_tasks.id)",
    )
    row_number: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Номер строки в исходном файле"
    )
    row_data: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="Сырые данные строки из файла"
    )
    error_description: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="Описание ошибок валидации строки"
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="Признак прохождения валидации"
    )
