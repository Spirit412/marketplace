"""create_notification_tables

Revision ID: a1b2c3d4e5f6
Revises: 02fa586d5a37
Create Date: 2026-07-26 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "02fa586d5a37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS "notification"')

    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_uuid", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("notification_type", sa.String(32), nullable=False, server_default=sa.text("'info'")),
        sa.Column("subject", sa.String(512), nullable=False, server_default=sa.text("''")),
        sa.Column("body", sa.Text, nullable=False, server_default=sa.text("''")),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'unread'"), index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("id"),
        schema="notification",
    )

    op.create_table(
        "templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(128), nullable=False, index=True),
        sa.Column("locale", sa.String(8), nullable=False, server_default=sa.text("'ru'")),
        sa.Column("subject", sa.String(512), nullable=False, server_default=sa.text("''")),
        sa.Column("body_template", sa.Text, nullable=False, server_default=sa.text("''")),
        sa.Column("channels", JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.UniqueConstraint("code", "locale", name="uq_template_code_locale"),
        schema="notification",
    )

    op.create_index("ix_notifications_created_at", "notifications",
                    ["created_at"], schema="notification")
    op.create_index("ix_notifications_status", "notifications",
                    ["status"], schema="notification")


def downgrade() -> None:
    op.drop_table("templates", schema="notification")
    op.drop_table("notifications", schema="notification")
    op.execute('DROP SCHEMA IF EXISTS "notification" CASCADE')
