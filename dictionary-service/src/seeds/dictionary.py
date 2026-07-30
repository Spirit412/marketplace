"""Idempotent seed script for dictionary-service.

Seeds three tables in the `dictionary` schema:
  - dictionary_entries
  - timezones
  - error_templates

Safe to run multiple times — uses INSERT … ON CONFLICT (upsert) for every row.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import settings
from src.models.dictionary import DictionaryEntry
from src.models.error_template import ErrorTemplate
from src.models.timezone import TimezoneEntry

logger = logging.getLogger(__name__)

SEEDS_DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_json(name: str) -> list | dict:
    path = SEEDS_DATA_DIR / name
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


async def _ensure_schema(session: AsyncSession) -> None:
    """Create the ``dictionary`` schema if it does not exist."""
    await session.execute(text("CREATE SCHEMA IF NOT EXISTS dictionary"))
    await session.commit()


async def seed_dictionary_entries(session: AsyncSession) -> int:
    """Seed ``dictionary_entries`` from ``dictionaries.json``.

    The JSON file is a dict keyed by dictionary type; each value is a list of
    entries with ``code`` and ``data`` fields.
    """
    raw: dict = _load_json("dictionaries.json")
    count = 0
    for type_name, entries in raw.items():
        for entry in entries:
            stmt = (
                pg_insert(DictionaryEntry)
                .values(
                    type=type_name,
                    code=entry["code"],
                    data=entry["data"],
                )
                .on_conflict_do_update(
                    index_elements=["type", "code"],
                    set_={"data": entry["data"]},
                )
            )
            await session.execute(stmt)
            count += 1
    await session.commit()
    logger.info("Seeded %d dictionary entries", count)
    return count


async def seed_timezones(session: AsyncSession) -> int:
    """Seed ``timezones`` from ``timezones.json``.

    Uses the unique ``iana_name`` column as the conflict target.
    """
    raw: list[dict] = _load_json("timezones.json")
    count = 0
    for row in raw:
        stmt = (
            pg_insert(TimezoneEntry)
            .values(
                iana_name=row["iana_name"],
                utc_offset=row["utc_offset"],
                display_name_ru=row["display_name_ru"],
                display_name_en=row["display_name_en"],
            )
            .on_conflict_do_update(
                index_elements=["iana_name"],
                set_={
                    "utc_offset": row["utc_offset"],
                    "display_name_ru": row["display_name_ru"],
                    "display_name_en": row["display_name_en"],
                },
            )
        )
        await session.execute(stmt)
        count += 1
    await session.commit()
    logger.info("Seeded %d timezone entries", count)
    return count


async def seed_error_templates(session: AsyncSession) -> int:
    """Seed ``error_templates`` from ``error_templates.json``.

    Uses the unique ``(code, locale)`` composite index as the conflict target.
    """
    raw: list[dict] = _load_json("error_templates.json")
    count = 0
    for row in raw:
        stmt = (
            pg_insert(ErrorTemplate)
            .values(
                code=row["code"],
                locale=row["locale"],
                message=row["message"],
                severity=row.get("severity", "info"),
            )
            .on_conflict_do_update(
                index_elements=["code", "locale"],
                set_={
                    "message": row["message"],
                    "severity": row.get("severity", "info"),
                },
            )
        )
        await session.execute(stmt)
        count += 1
    await session.commit()
    logger.info("Seeded %d error templates", count)
    return count


async def run_all() -> dict[str, int]:
    """Run every seed function and return per-table counts."""
    engine = create_async_engine(
        settings.postgres.dsn,
        echo=False,
        pool_pre_ping=True,
    )
    factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with factory() as session:
        await _ensure_schema(session)
        counts: dict[str, int] = {}

        logger.info("Seeding dictionary entries …")
        counts["dictionary_entries"] = await seed_dictionary_entries(session)

        logger.info("Seeding timezones …")
        counts["timezones"] = await seed_timezones(session)

        logger.info("Seeding error templates …")
        counts["error_templates"] = await seed_error_templates(session)

    await engine.dispose()
    return counts


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)-5s %(name)s %(message)s",
    )

    async def _main() -> None:
        counts = await run_all()
        print(f"\nSeeding complete: {counts}")

    asyncio.run(_main())
