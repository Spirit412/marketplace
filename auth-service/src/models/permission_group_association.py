from uuid import UUID

from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class PermissionGroupAssociation(TimestampMixin, Base):
    __tablename__ = "permission_group_association"
    __table_args__ = (
        PrimaryKeyConstraint("group_id", "permission_id"),
        Index(None, "group_id", "permission_id"),
        {"schema": "auth", "comment": "Связь группы прав-разрешение"},
    )

    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth.groups.id", ondelete="CASCADE"), comment="fk на группу"
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth.permissions.id", ondelete="CASCADE"),
        comment="fk на разрешение",
    )
