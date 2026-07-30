from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.datatype import uuid7
from src.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from src.models.user_access import UserAccess


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    __table_args__ = {
        "schema": "auth",
        "comment": "Пользователь (покупатель, продавец, модератор, админ)",
    }

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ пользователя"
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        comment="Email, используется для входа",
    )
    password_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="Хеш пароля"
    )

    timezone: Mapped[str] = mapped_column(
        String(64), default="UTC", comment="Часовой пояс пользователя (IANA-имя)"
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="Признак блокировки учётной записи"
    )
    blocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Дата и время блокировки"
    )
    blocked_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("auth.users.id"),
        nullable=True,
        comment="Кто заблокировал пользователя (fk на users.id)",
    )
    block_reason: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Причина блокировки"
    )
    user_accesses: Mapped[list[UserAccess]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    sessions: Mapped[list[SessionLog]] = relationship(
        back_populates="user", lazy="selectin"
    )


class SessionLog(TimestampMixin, Base):
    __tablename__ = "session_logs"
    __table_args__ = {
        "schema": "auth",
        "comment": "История сессий входа пользователя (для аудита и статистики)",
    }

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="Первичный ключ записи сессии"
    )
    user_uuid: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Пользователь, которому принадлежит сессия",
    )
    login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Дата и время входа",
    )
    logout_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время выхода (NULL — сессия активна)",
    )
    refresh_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Сколько раз обновлялся access-токен в рамках сессии",
    )
    device_info: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="User-Agent устройства входа"
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True, comment="IP-адрес при входе"
    )
    session_jti: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="JWT ID (jti) токена, выданного при входе"
    )

    user: Mapped[User] = relationship(back_populates="sessions")
