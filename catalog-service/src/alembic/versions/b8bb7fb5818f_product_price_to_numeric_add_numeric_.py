"""product price to numeric, add numeric_properties

Revision ID: b8bb7fb5818f
Revises: 4b54f2f5e936
Create Date: 2026-07-29 13:54:18.508121
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b8bb7fb5818f"
down_revision: Union[str, None] = "4b54f2f5e936"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "numeric_properties",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        schema="catalog",
    )
    op.alter_column(
        "products",
        "price",
        existing_type=sa.DOUBLE_PRECISION(precision=53),
        type_=sa.Numeric(precision=12, scale=2),
        existing_nullable=False,
        schema="catalog",
    )
    op.create_index(
        "ix_products_numeric_properties",
        "products",
        ["numeric_properties"],
        unique=False,
        schema="catalog",
        postgresql_using="gin",
        postgresql_ops={"numeric_properties": "jsonb_path_ops"},
    )
    op.create_index(
        "ix_products_price", "products", ["price"], unique=False, schema="catalog"
    )


def downgrade() -> None:
    op.drop_index("ix_products_price", table_name="products", schema="catalog")
    op.drop_index(
        "ix_products_numeric_properties",
        table_name="products",
        schema="catalog",
        postgresql_using="gin",
        postgresql_ops={"numeric_properties": "jsonb_path_ops"},
    )
    op.alter_column(
        "products",
        "price",
        existing_type=sa.Numeric(precision=12, scale=2),
        type_=sa.DOUBLE_PRECISION(precision=53),
        existing_nullable=False,
        schema="catalog",
    )
    op.drop_column("products", "numeric_properties", schema="catalog")
