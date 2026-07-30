"""initial

Revision ID: 4b54f2f5e936
Revises:
Create Date: 2026-07-26 18:24:16.754959
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "4b54f2f5e936"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("lft", sa.Integer(), nullable=False),
        sa.Column("rgt", sa.Integer(), nullable=False),
        sa.Column("tree_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["catalog.categories.id"],
            name=op.f("fk_categories_parent_id_categories"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("slug", name=op.f("uq_categories_slug")),
        schema="catalog",
    )
    op.create_table(
        "properties",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("backend_name", sa.String(length=255), nullable=False),
        sa.Column("frontend_label", sa.String(length=255), nullable=False),
        sa.Column("property_type", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_properties")),
        sa.UniqueConstraint("backend_name", name=op.f("uq_properties_backend_name")),
        schema="catalog",
    )
    op.create_table(
        "query_sets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "displayed_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_query_sets")),
        schema="catalog",
    )
    op.create_index(
        op.f("ix_catalog_query_sets_seller_id"),
        "query_sets",
        ["seller_id"],
        unique=False,
        schema="catalog",
    )
    op.create_table(
        "category_properties",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("property_id", sa.Uuid(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["catalog.categories.id"],
            name=op.f("fk_category_properties_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["catalog.properties.id"],
            name=op.f("fk_category_properties_property_id_properties"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_category_properties")),
        schema="catalog",
    )
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("sku", sa.String(length=100), nullable=True),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column(
            "custom_properties_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["catalog.categories.id"],
            name=op.f("fk_products_category_id_categories"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
        sa.UniqueConstraint("sku", name=op.f("uq_products_sku")),
        schema="catalog",
    )
    op.create_index(
        op.f("ix_catalog_products_seller_id"),
        "products",
        ["seller_id"],
        unique=False,
        schema="catalog",
    )
    op.create_index(
        "ix_products_category_id",
        "products",
        ["category_id"],
        unique=False,
        schema="catalog",
    )
    op.create_index(
        "ix_products_custom_properties",
        "products",
        ["custom_properties_config"],
        unique=False,
        schema="catalog",
        postgresql_using="gin",
    )
    op.create_index(
        "ix_products_is_active",
        "products",
        ["is_active"],
        unique=False,
        schema="catalog",
    )
    op.create_index(
        "ix_products_search_vector",
        "products",
        ["search_vector"],
        unique=False,
        schema="catalog",
        postgresql_using="gin",
    )
    op.create_index(
        "ix_products_seller_id",
        "products",
        ["seller_id"],
        unique=False,
        schema="catalog",
    )


def downgrade() -> None:
    op.drop_index("ix_products_seller_id", table_name="products", schema="catalog")
    op.drop_index(
        "ix_products_search_vector",
        table_name="products",
        schema="catalog",
        postgresql_using="gin",
    )
    op.drop_index("ix_products_is_active", table_name="products", schema="catalog")
    op.drop_index(
        "ix_products_custom_properties",
        table_name="products",
        schema="catalog",
        postgresql_using="gin",
    )
    op.drop_index("ix_products_category_id", table_name="products", schema="catalog")
    op.drop_index(
        op.f("ix_catalog_products_seller_id"), table_name="products", schema="catalog"
    )
    op.drop_table("products", schema="catalog")
    op.drop_table("category_properties", schema="catalog")
    op.drop_index(
        op.f("ix_catalog_query_sets_seller_id"),
        table_name="query_sets",
        schema="catalog",
    )
    op.drop_table("query_sets", schema="catalog")
    op.drop_table("properties", schema="catalog")
    op.drop_table("categories", schema="catalog")
