"""Test fixtures for auth-service."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.main import app
from src.config.settings import settings

TEST_EMAIL_PREFIX = "pytest."


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Real session against the shared dev Postgres (auth schema).

    Tables already exist via Alembic — this fixture does not create/drop the
    schema, it only gives tests a session. Use uniquely-prefixed test data
    (see TEST_EMAIL_PREFIX below) so runs don't collide with seeded demo users.
    """
    engine = create_async_engine(settings.postgres.dsn, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(autouse=True)
async def _cleanup_test_users(db_session: AsyncSession) -> AsyncGenerator[None, None]:
    """Delete any pytest.* users before and after each test — keeps tests idempotent
    and re-runnable without leaving junk rows in the shared dev database."""

    async def _delete() -> None:
        await db_session.execute(
            text("DELETE FROM auth.users WHERE email LIKE :pattern"),
            {"pattern": f"{TEST_EMAIL_PREFIX}%"},
        )
        await db_session.commit()

    await _delete()
    yield
    await _delete()
