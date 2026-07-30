import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.datatype import uuid7
from src.models.base import SoftDeleteMixin, TimestampMixin
from src.models.dictionary import Base


class TimezoneEntry(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "timezones"
    __table_args__ = {
        "schema": "dictionary",
        "comment": "Справочник часовых поясов (IANA)",
    }

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ записи"
    )
    iana_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="IANA-имя часового пояса (Europe/Moscow)",
    )
    utc_offset: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="Смещение от UTC (+03:00)"
    )
    display_name_ru: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Название на русском"
    )
    display_name_en: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Название на английском"
    )
