from uuid import UUID

from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RoleGroupAssociation(TimestampMixin, Base):
    __tablename__ = "role_group_association"
    __table_args__ = (
        PrimaryKeyConstraint("role_id", "group_id"),
        Index(None, "role_id", "group_id"),
        {"schema": "auth", "comment": "Связь роль-группа прав"},
    )

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth.roles.id", ondelete="CASCADE"), comment="fk роли"
    )
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth.groups.id", ondelete="CASCADE"), comment="fk группы"
    )
