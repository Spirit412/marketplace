from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.datatype import uuid7
from src.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .permission import Permission
    from .role import Role


class Group(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "groups"
    __table_args__ = {"schema": "auth", "comment": "Группа прав — объединяет разрешения (Permission), назначается ролям"}

    uuid: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid7, comment="pk группы"
    )
    name: Mapped[str] = mapped_column(comment="название группы")
    description: Mapped[str | None] = mapped_column(comment="описание группы")


    roles: Mapped[list[Role]] = relationship(
        secondary="auth.role_group_association", back_populates="groups"
    )
    permissions: Mapped[list[Permission]] = relationship(
        secondary="auth.permission_group_association", back_populates="groups"
    )

    def __repr__(self) -> str:
        return f"<Group {self.uuid} {self.name}>"
