"""create warehouses stock_items stock_movements tables

Revision ID: d4354e84772e
Revises: 560b692e9c8d
Create Date: 2026-07-29 15:10:32.513756
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4354e84772e"
down_revision: Union[str, None] = "560b692e9c8d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "warehouses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("seller_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_warehouses")),
        sa.UniqueConstraint("seller_id", "name", name="uq_warehouse_seller_name"),
        schema="inventory",
    )
    op.create_table(
        "stock_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("warehouse_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reserved", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["warehouse_id"],
            ["inventory.warehouses.id"],
            name=op.f("fk_stock_items_warehouse_id_warehouses"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stock_items")),
        schema="inventory",
    )
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("stock_item_id", sa.UUID(), nullable=False),
        sa.Column("movement_type", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["stock_item_id"],
            ["inventory.stock_items.id"],
            name=op.f("fk_stock_movements_stock_item_id_stock_items"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stock_movements")),
        schema="inventory",
    )


def downgrade() -> None:
    op.drop_table("stock_movements", schema="inventory")
    op.drop_table("stock_items", schema="inventory")
    op.drop_table("warehouses", schema="inventory")
