"""Seed script — populate report templates from JSON data.

Idempotent: safe to run multiple times (upserts by name).

Data files:
    seeds/data/report_templates.json   — [{name, sql_template, parameters_schema}, ...]

Usage:
    poetry run python -m src.seeds.seed_report_templates
"""

import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import settings
from src.models.report import ReportTemplate

DATA_DIR = Path(__file__).parent / "data"


def _load_json(name: str) -> list | dict:
    with open(DATA_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


async def seed_report_templates(session: AsyncSession) -> None:
    """Upsert report templates from JSON data by name. Idempotent."""
    templates = _load_json("report_templates.json")
    count_created = 0
    count_updated = 0

    for tmpl in templates:
        name = tmpl["name"]
        stmt = select(ReportTemplate).where(ReportTemplate.name == name)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            session.add(
                ReportTemplate(
                    name=name,
                    sql_template=tmpl["sql_template"],
                    parameters_schema=tmpl["parameters_schema"],
                )
            )
            count_created += 1
            print(f"  + Created template: {name}")
        else:
            existing.sql_template = tmpl["sql_template"]
            existing.parameters_schema = tmpl["parameters_schema"]
            count_updated += 1
            print(f"  ~ Updated template: {name}")

    await session.flush()
    print(f"\nSeed complete: {count_created} created, {count_updated} updated.")


async def _main() -> None:
    engine = create_async_engine(settings.postgres.dsn)
    session_factory = async_sessionmaker(engine, class_=AsyncSession)

    async with session_factory() as session:
        try:
            await seed_report_templates(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
