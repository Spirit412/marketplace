"""Seed script — populates catalog.products from JSON, for a fixed demo seller.

Idempotent: safe to run multiple times (checks existence by `sku`, the model's
actual unique key — the JSON fixture's "slug" field is only used to reference
a product from other seed data, e.g. inventory cells; Product has no slug column).

Requires the auth-service RBAC seed (src.seeds.rbac in auth-service) to have
already run, so the demo seller user exists — this script looks it up by email
directly via SQL against auth.users, since all services share one PostgreSQL
instance (see "Детальная архитектура", раздел 1) even though they're separate
codebases with separate schemas.

Data file:
    seeds/data/products.json — [{slug, name, description, category_slug, price,
                                 sku, stock, custom_properties_config,
                                 numeric_properties}, ...]

Usage:
    poetry run python -m src.seeds.products
    poetry run python -m src.seeds.products --seller-email seller@marketplace.dev
"""

import argparse
import asyncio
import json
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import settings
from src.models.category import Category
from src.models.product import Product

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_SELLER_EMAIL = "seller@marketplace.dev"


def _load_json(name: str) -> list[dict[str, Any]]:
    with (DATA_DIR / name).open(encoding="utf-8") as fh:
        data: list[dict[str, Any]] = json.load(fh)
        return data


async def _resolve_seller_id(session: AsyncSession, email: str) -> UUID:
    result = await session.execute(
        text("SELECT id FROM auth.users WHERE email = :email"),
        {"email": email},
    )
    row = result.first()
    if row is None:
        raise RuntimeError(
            f"Seller user '{email}' not found in auth.users — "
            "run auth-service's `python -m src.seeds.rbac` first."
        )
    seller_id: UUID = row[0]
    return seller_id


async def seed_products(
    session: AsyncSession, *, seller_email: str = DEFAULT_SELLER_EMAIL
) -> None:
    """Populate catalog.products from products.json. Idempotent by `sku`."""
    seller_id = await _resolve_seller_id(session, seller_email)

    products_data = _load_json("products.json")

    created = 0
    skipped = 0
    for entry in products_data:
        existing = await session.execute(
            select(Product).where(Product.sku == entry["sku"])
        )
        if existing.scalar_one_or_none() is not None:
            skipped += 1
            continue

        category_id = None
        if entry.get("category_slug"):
            cat_result = await session.execute(
                select(Category.id).where(Category.slug == entry["category_slug"])
            )
            category_row = cat_result.first()
            if category_row is not None:
                category_id = category_row[0]

        product = Product(
            seller_id=seller_id,
            category_id=category_id,
            name=entry["name"],
            description=entry.get("description"),
            price=Decimal(entry["price"]),
            sku=entry["sku"],
            stock=entry.get("stock", 0),
            custom_properties_config=entry.get("custom_properties_config", {}),
            numeric_properties=entry.get("numeric_properties", {}),
            is_active=True,
            status="active",
        )
        session.add(product)
        created += 1

    await session.commit()
    print(
        f"Products: {created} created, {skipped} already existed "
        f"(seller={seller_email})"
    )


async def _main(seller_email: str) -> None:
    engine = create_async_engine(settings.postgres.dsn, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        try:
            await seed_products(session, seller_email=seller_email)
        finally:
            await session.close()
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seller-email", default=DEFAULT_SELLER_EMAIL)
    args = parser.parse_args()
    asyncio.run(_main(args.seller_email))
