from uuid import UUID

from sqlalchemy import ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class PermissionGroupAssociation(TimestampMixin, Base):
    __tablename__ = "permission_group_association"
    __table_args__ = (
        PrimaryKeyConstraint("group_uuid", "permission_uuid"),
        Index(None, "group_uuid", "permission_uuid"),
        {"schema": "auth", "comment": "Связь группы прав-разрешение"},
    )

    group_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("auth.groups.uuid", ondelete="CASCADE"), comment="fk на группу"
    )
    permission_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("auth.permissions.uuid", ondelete="CASCADE"), comment="fk на разрешение"
    )

