from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import false

from src.core.datatype import uuid7
from src.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .group import Group
    from .user_access import UserAccess


class Role(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "auth", "comment": "Роль пользователя"}

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid7,
        comment="pk роли",
    )
    name: Mapped[str] = mapped_column(comment="название роли")
    description: Mapped[str | None] = mapped_column(
        default=None,
        comment="описание роли",
    )
    is_admin: Mapped[bool] = mapped_column(
        default=False,
        server_default=false(),
        comment="признак административной роли",
    )

    groups: Mapped[list[Group]] = relationship(
        secondary="auth.role_group_association",
        back_populates="roles",
    )
    user_accesses: Mapped[list[UserAccess]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role {self.id} {self.name}>"
