from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from .permission import Permission
    from .role import Role
    from .user import User


class UserAccess(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "user_access"
    __table_args__ = (
        PrimaryKeyConstraint("user_id"),
        Index(None, "user_id", "role_uuid"),
        {
            "schema": "auth",
            "comment": "Назначенные пользователю роль и дополнительные разрешения",
        },
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        comment="fk пользователя",
    )
    role_uuid: Mapped[UUID | None] = mapped_column(
        ForeignKey("auth.roles.uuid", ondelete="SET NULL"),
        default=None,
        comment="fk роли",
    )
    additional_permissions: Mapped[list[UUID]] = mapped_column(
        default=list,
        comment="дополнительные разрешения пользователя",
    )

    role: Mapped[Role | None] = relationship(
        back_populates="user_accesses",
        lazy="selectin",
    )
    user: Mapped[User] = relationship(
        back_populates="user_accesses",
        lazy="selectin",
    )

    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        primaryjoin=(
            "remote(Permission.uuid) == "
            "func.any_(foreign(UserAccess.additional_permissions))"
        ),
        viewonly=True,
        lazy="selectin",
        uselist=True,
    )

    def __repr__(self) -> str:
        return (
            f"<UserAccess user={self.user_id} "
            f"role={self.role_uuid} "
            f"additional={self.additional_permissions}>"
        )
