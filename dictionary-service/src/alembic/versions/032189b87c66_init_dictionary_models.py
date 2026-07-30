"""init_dictionary_models

Revision ID: 032189b87c66
Revises:
Create Date: 2026-07-26 18:21:09.019337
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "032189b87c66"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dictionary_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=255), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dictionary_entries")),
        schema="dictionary",
    )
    op.create_index(
        op.f("ix_dictionary_dictionary_entries_type"),
        "dictionary_entries",
        ["type"],
        unique=False,
        schema="dictionary",
    )
    op.create_index(
        "ix_dictionary_entries_type_code",
        "dictionary_entries",
        ["type", "code"],
        unique=True,
        schema="dictionary",
    )
    op.create_table(
        "error_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("locale", sa.String(length=10), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_error_templates")),
        schema="dictionary",
    )
    op.create_index(
        "ix_error_templates_code_locale",
        "error_templates",
        ["code", "locale"],
        unique=True,
        schema="dictionary",
    )
    op.create_table(
        "timezones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("iana_name", sa.String(length=100), nullable=False),
        sa.Column("utc_offset", sa.String(length=10), nullable=False),
        sa.Column("display_name_ru", sa.String(length=200), nullable=False),
        sa.Column("display_name_en", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_timezones")),
        sa.UniqueConstraint(
            "iana_name", name=op.f("uq_timezones_iana_name")
        ),
        schema="dictionary",
    )


def downgrade() -> None:
    op.drop_table("timezones", schema="dictionary")
    op.drop_index(
        "ix_error_templates_code_locale",
        table_name="error_templates",
        schema="dictionary",
    )
    op.drop_table("error_templates", schema="dictionary")
    op.drop_index(
        "ix_dictionary_entries_type_code",
        table_name="dictionary_entries",
        schema="dictionary",
    )
    op.drop_index(
        op.f("ix_dictionary_dictionary_entries_type"),
        table_name="dictionary_entries",
        schema="dictionary",
    )
    op.drop_table("dictionary_entries", schema="dictionary")
