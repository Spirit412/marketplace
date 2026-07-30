from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.datatype import uuid7
from src.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .groups import Group


class Permission(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "permissions"
    __table_args__ = {"schema": "auth", "comment": "Разрешение — доступ к конкретному методу и пути одного микросервиса"}

    uuid: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="pk разрешения"
    )
    name: Mapped[str] = mapped_column(comment="название разрешения")
    app_id: Mapped[str] = mapped_column(comment="идентификатор микросервиса")
    method: Mapped[str] = mapped_column(comment="HTTP-метод")
    path: Mapped[str] = mapped_column(comment="путь для доступа")


    groups: Mapped[list[Group]] = relationship(
        secondary="auth.permission_group_association", back_populates="permissions"
    )

    def __repr__(self) -> str:
        return f"<Permission {self.uuid} {self.app_id}:{self.method} {self.path}>"
