"""Idempotent seed script for notification templates.

Usage:
    python -m src.seeds.seed_templates
    # or override DSN for local dev:
    POSTGRES_DSN="postgresql+asyncpg://user:pass@localhost:5432/db" python -m src.seeds.seed_templates

Upserts templates from templates_data.json — if a template with the same
(code, locale) already exists, its fields are updated rather than duplicated.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    String,
    Text,
    UniqueConstraint,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parent / "templates_data.json"
DEFAULT_DSN = (
    "postgresql+asyncpg://marketplace:marketplace@mp-postgres:5432/marketplace"
)


def _uuid7() -> uuid.UUID:
    """Local copy of src/core/datatype.py's uuid7() — this script deliberately
    avoids importing src/ (see module docstring), so the id generator is
    copied rather than shared, same as every other core/ file in this codebase.
    """
    rand_bytes = os.urandom(8)
    hex_str = f"{int(time.time() * 1000):016x}{rand_bytes.hex()}"
    hex_list = list(hex_str)
    hex_list[12] = "7"
    hex_list[16] = "8"
    return uuid.UUID(hex="".join(hex_list))


class _Base(DeclarativeBase):
    pass


class _Template(_Base):
    """Local model mirror — avoids import of src/ which has broken import chains."""

    __tablename__ = "templates"
    __table_args__ = (
        UniqueConstraint("code", "locale", name="uq_template_code_locale"),
        {"schema": "notification"},
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=_uuid7)
    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    locale: Mapped[str] = mapped_column(String(8), nullable=False, default="ru")
    subject: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    body_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    channels: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


def _load_seed_data() -> list[dict]:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


async def _ensure_schema(conn):
    await conn.execute(text('CREATE SCHEMA IF NOT EXISTS "notification"'))
    await conn.commit()


async def _upsert_template(session: AsyncSession, data: dict) -> _Template:
    """Upsert a single template by (code, locale). Returns the _Template."""
    stmt = select(_Template).where(
        _Template.code == data["code"],
        _Template.locale == data["locale"],
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is not None:
        existing.subject = data["subject"]
        existing.body_template = data["body_template"]
        existing.channels = data.get("channels")
        existing.is_active = data.get("is_active", True)
        existing.updated_at = datetime.now(UTC)
        template = existing
    else:
        template = _Template(
            id=_uuid7(),
            code=data["code"],
            locale=data["locale"],
            subject=data["subject"],
            body_template=data["body_template"],
            channels=data.get("channels"),
            is_active=data.get("is_active", True),
        )
        session.add(template)

    await session.flush()
    return template


async def seed_templates(dsn: str | None = None) -> int:
    """Run the seed: upsert all templates from JSON data.

    Returns the number of templates upserted.
    """
    connection_string = dsn or os.environ.get("POSTGRES_DSN") or DEFAULT_DSN
    engine = create_async_engine(connection_string, echo=False)

    async with engine.begin() as conn:
        await _ensure_schema(conn)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    items = _load_seed_data()
    logger.info("Seeding %d template entries …", len(items))

    async with session_factory() as session, session.begin():
        for entry in items:
            await _upsert_template(session, entry)

    await engine.dispose()
    return len(items)


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    count = await seed_templates()
    logger.info("Done — %d templates upserted.", count)


if __name__ == "__main__":
    asyncio.run(main())
