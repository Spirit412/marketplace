from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_postgres(session: AsyncSession) -> None:
    await session.execute(text("SELECT 1"))


async def init_db(session: AsyncSession) -> None:
    """Create notification schema if not exists."""
    await session.execute(text("CREATE SCHEMA IF NOT EXISTS notification"))
    await session.commit()
