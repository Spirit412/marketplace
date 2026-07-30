from uuid import UUID

from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class RoleGroupAssociation(TimestampMixin, Base):
    __tablename__ = "role_group_association"
    __table_args__ = (
        PrimaryKeyConstraint("role_uuid", "group_uuid"),
        Index(None, "role_uuid", "group_uuid"),
        {"schema": "auth", "comment": "Связь роль-группа прав"},
    )

    role_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("auth.roles.uuid", ondelete="CASCADE"), comment="fk роли"
    )
    group_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("auth.groups.uuid", ondelete="CASCADE"), comment="fk группы"
    )

