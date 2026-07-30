"""Seed script — creates one demo warehouse + stock for the seeded catalog products.

Idempotent: warehouse upserted by (seller_id, name) unique constraint;
stock items upserted by (warehouse_id, product_id).

Requires, in order:
    auth-service:    python -m src.seeds.rbac       (creates the demo seller)
    catalog-service: python -m src.seeds.products    (creates the demo products)

Looks up the seller and products directly via SQL against auth.users /
catalog.products — all services share one PostgreSQL instance (see
"Детальная архитектура", раздел 1), so a cross-schema read here is a plain
query, not a network call.

Usage:
    poetry run python -m src.seeds.stock
"""

import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import settings
from src.enums.movement_type import MovementType
from src.models.models import StockItem, StockMovement, Warehouse

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_SELLER_EMAIL = "seller@marketplace.dev"


def _load_json(name: str) -> dict[str, Any]:
    with open(DATA_DIR / name, encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
        return data


async def _resolve_seller_id(session: AsyncSession, email: str) -> UUID:
    result = await session.execute(
        text("SELECT id FROM auth.users WHERE email = :email"), {"email": email}
    )
    row = result.first()
    if row is None:
        raise RuntimeError(
            f"Seller user '{email}' not found — run auth-service's `python -m src.seeds.rbac` first."
        )
    seller_id: UUID = row[0]
    return seller_id


async def _resolve_product_ids(
    session: AsyncSession, skus: list[str]
) -> dict[str, UUID]:
    result = await session.execute(
        text("SELECT sku, id FROM catalog.products WHERE sku = ANY(:skus)"),
        {"skus": skus},
    )
    found = {sku: pid for sku, pid in result.all()}
    missing = set(skus) - set(found)
    if missing:
        raise RuntimeError(
            f"Products not found for SKUs {sorted(missing)} — "
            "run catalog-service's `python -m src.seeds.products` first."
        )
    return found


async def seed_stock(
    session: AsyncSession, *, seller_email: str = DEFAULT_SELLER_EMAIL
) -> None:
    """Populate one warehouse + stock items for the seeded demo products. Idempotent."""
    data = _load_json("stock.json")
    seller_id = await _resolve_seller_id(session, seller_email)
    product_ids = await _resolve_product_ids(session, data["skus"])

    warehouse_cfg = data["warehouse"]
    existing_wh = await session.execute(
        select(Warehouse).where(
            Warehouse.seller_id == seller_id, Warehouse.name == warehouse_cfg["name"]
        )
    )
    warehouse = existing_wh.scalar_one_or_none()
    if warehouse is None:
        warehouse = Warehouse(
            seller_id=seller_id,
            name=warehouse_cfg["name"],
            address=warehouse_cfg.get("address"),
            timezone=warehouse_cfg.get("timezone", "UTC"),
        )
        session.add(warehouse)
        await session.flush()

    quantity = data.get("quantity_per_sku", 100)
    created = 0
    skipped = 0
    for sku, product_id in product_ids.items():
        existing_item = await session.execute(
            select(StockItem).where(
                StockItem.warehouse_id == warehouse.id,
                StockItem.product_id == product_id,
            )
        )
        stock_item = existing_item.scalar_one_or_none()
        if stock_item is not None:
            skipped += 1
            continue

        stock_item = StockItem(
            product_id=product_id,
            warehouse_id=warehouse.id,
            quantity=quantity,
            reserved=0,
        )
        session.add(stock_item)
        await session.flush()

        session.add(
            StockMovement(
                stock_item_id=stock_item.id,
                movement_type=MovementType.RECEIPT,
                quantity=quantity,
                reference_type="seed",
                reference_id=None,
            )
        )
        created += 1

    await session.commit()
    print(
        f"Stock: warehouse '{warehouse.name}' ready, {created} items created, {skipped} already existed"
    )


async def _main(seller_email: str) -> None:
    engine = create_async_engine(settings.postgres.dsn, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        try:
            await seed_stock(session, seller_email=seller_email)
        finally:
            await session.close()
    await engine.dispose()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seller-email", default=DEFAULT_SELLER_EMAIL)
    args = parser.parse_args()
    asyncio.run(_main(args.seller_email))
