"""Seed script — populates catalog DB from JSON data files.

Idempotent: safe to run multiple times (checks by slug/backend_name).

Data files:
    seeds/data/categories.json   — [{name, slug, description, children: [...]}, ...]
    seeds/data/properties.json   — [{backend_name, frontend_label, property_type,
                                     options, category_slugs}, ...]

Usage:
    POSTGRES_HOST=localhost poetry run python -m src.seeds.catalog
"""

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import settings
from src.core.datatype import uuid7
from src.models.category import Category
from src.models.property import CategoryProperty, Property

if TYPE_CHECKING:
    import uuid

DATA_DIR = Path(__file__).parent / "data"


def _load_json(name: str) -> Any:
    """Load a seed data file.

    Returns `Any`: callers annotate the variable with the shape that
    specific file actually holds.
    """
    with (DATA_DIR / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def _compute_mptt(
    nodes: list[dict[str, Any]], tree_id_start: int = 0
) -> list[dict[str, Any]]:
    """Walk nested category tree and fill in MPTT fields in-place.

    Each node receives ``tree_id``, ``level``, ``lft``, ``rgt``.
    Returns the same list for convenience.
    """

    def _walk(
        node: dict[str, Any],
        tree_id: int,
        level: int,
        counter: list[int],
        parent_slug: str | None = None,
    ) -> None:
        node["tree_id"] = tree_id
        node["level"] = level
        node["lft"] = counter[0]
        counter[0] += 1
        if parent_slug is not None:
            node["parent_slug"] = parent_slug
        for child in node.get("children", []):
            _walk(child, tree_id, level + 1, counter, node["slug"])
        node["rgt"] = counter[0]
        counter[0] += 1

    next_id = tree_id_start
    for root in nodes:
        _walk(root, next_id, 0, [1])
        next_id += 1
    return nodes


def _flatten(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a flat list of all nodes (breadth-first) from a nested tree."""
    result: list[dict[str, Any]] = []
    queue = list(nodes)
    while queue:
        node = queue.pop(0)
        children = node.pop("children", [])
        result.append(node)
        queue.extend(children)
    return result


async def seed_catalog(session: AsyncSession) -> None:
    """Populate DB from JSON data files. Idempotent."""
    print("[1/2] Categories...")
    categories_data: list[dict[str, Any]] = _load_json("categories.json")
    _compute_mptt(categories_data)
    flat_categories = _flatten(categories_data)

    slug_to_id: dict[str, uuid.UUID] = {}
    for entry in flat_categories:
        existing = await session.execute(
            select(Category).where(Category.slug == entry["slug"])
        )
        existing_cat = existing.scalar_one_or_none()
        if existing_cat is not None:
            slug_to_id[entry["slug"]] = existing_cat.id
            continue

        parent_id = None
        if entry["level"] > 0:
            parent_id = slug_to_id.get(entry.get("parent_slug", ""))

        category = Category(
            id=uuid7(),
            name=entry["name"],
            slug=entry["slug"],
            description=entry.get("description"),
            parent_id=parent_id,
            lft=entry["lft"],
            rgt=entry["rgt"],
            tree_id=entry["tree_id"],
            level=entry["level"],
        )
        session.add(category)
        await session.flush()
        slug_to_id[entry["slug"]] = category.id

    print(f"  {len(slug_to_id)} categories ready")

    print("[2/2] Properties...")
    properties_data: list[dict[str, Any]] = _load_json("properties.json")

    backend_to_id: dict[str, uuid.UUID] = {}
    for entry in properties_data:
        existing = await session.execute(
            select(Property).where(Property.backend_name == entry["backend_name"])
        )
        existing_prop = existing.scalar_one_or_none()
        if existing_prop is not None:
            backend_to_id[entry["backend_name"]] = existing_prop.id
            continue

        prop = Property(
            id=uuid7(),
            backend_name=entry["backend_name"],
            frontend_label=entry["frontend_label"],
            property_type=entry["property_type"],
            description=entry.get("description"),
            options=entry.get("options", {}),
        )
        session.add(prop)
        await session.flush()
        backend_to_id[entry["backend_name"]] = prop.id

    print(f"  {len(backend_to_id)} properties ready")

    print("[+] Linking properties to categories...")
    link_count = 0
    for entry in properties_data:
        prop_id = backend_to_id.get(entry["backend_name"])
        if prop_id is None:
            continue
        for cat_slug in entry.get("category_slugs", []):
            cat_id = slug_to_id.get(cat_slug)
            if cat_id is None:
                continue

            existing_link = await session.execute(
                select(CategoryProperty).where(
                    CategoryProperty.category_id == cat_id,
                    CategoryProperty.property_id == prop_id,
                )
            )
            if existing_link.scalar_one_or_none() is not None:
                continue

            link = CategoryProperty(
                id=uuid7(),
                category_id=cat_id,
                property_id=prop_id,
                is_required=False,
                sort_order=0,
            )
            session.add(link)
            link_count += 1

    print(f"  {link_count} links created")

    await session.commit()
    print("Seed complete.")


async def _main() -> None:
    engine = create_async_engine(settings.postgres.dsn, echo=False)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        try:
            await seed_catalog(session)
        finally:
            await session.close()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
