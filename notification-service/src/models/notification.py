from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.datatype import uuid7
from src.models.base import Base, CreatedAtMixin, SoftDeleteMixin, TimestampMixin


class Notification(CreatedAtMixin, SoftDeleteMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index(None, "created_at"),
        {
            "schema": "notification",
            "comment": "Уведомление пользователю (email/sms/push/websocket)",
        },
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ уведомления"
    )
    user_id: Mapped[UUID] = mapped_column(
        index=True, nullable=False, comment="Получатель уведомления"
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Событие-источник (order.created и т.п.)",
    )
    channel: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="Канал доставки (email/sms/push/websocket)"
    )
    notification_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="info",
        comment="Тип уведомления (info/warning/error/success)",
    )
    subject: Mapped[str] = mapped_column(
        String(512), nullable=False, default="", comment="Заголовок уведомления"
    )
    body: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="Текст уведомления"
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="unread",
        index=True,
        comment="Статус доставки/прочтения",
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата прочтения уведомления"
    )


class Template(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("code", "locale", name="uq_template_code_locale"),
        {
            "schema": "notification",
            "comment": "Шаблон текста уведомления (Jinja2, локализованный)",
        },
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ шаблона"
    )
    code: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="Код шаблона (обычно совпадает с типом события)",
    )
    locale: Mapped[str] = mapped_column(
        String(8), nullable=False, default="ru", comment="Локаль шаблона"
    )
    subject: Mapped[str] = mapped_column(
        String(512), nullable=False, default="", comment="Шаблон заголовка"
    )
    body_template: Mapped[str] = mapped_column(
        Text, nullable=False, default="", comment="Шаблон текста сообщения"
    )
    channels: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True, comment="Каналы, для которых применим шаблон"
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, comment="Признак активности шаблона"
    )
