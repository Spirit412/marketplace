from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings


async def check_postgres(session: AsyncSession) -> None:
    await session.execute(text("SELECT 1"))


async def init_db(session: AsyncSession) -> None:
    """Create schema if not exists."""
    await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.DB_SCHEMA}"))
    await session.commit()
