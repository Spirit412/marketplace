"""Test fixtures for dictionary-service."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import get_settings
from src.core.datatype import uuid7
from src.models.dictionary import Base, DictionaryEntry


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create async engine for test database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    test_engine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create per-test database session with rollback."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def test_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP test client."""
    from src.main import app
    from src.repositories.dictionary_repo import DictionaryRepository

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[
        "get_async_session"
    ] = override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_dictionary(db_session: AsyncSession) -> list[DictionaryEntry]:
    """Seed test dictionary entries."""
    entries = [
        DictionaryEntry(
            id=uuid7(),
            type="countries",
            code="RU",
            data={"name_ru": "Россия", "name_en": "Russia", "iso_alpha2": "RU"},
        ),
        DictionaryEntry(
            id=uuid7(),
            type="countries",
            code="US",
            data={"name_ru": "США", "name_en": "USA", "iso_alpha2": "US"},
        ),
        DictionaryEntry(
            id=uuid7(),
            type="currencies",
            code="RUB",
            data={"code": "RUB", "name": "Российский рубль", "rate": 1.0},
        ),
    ]
    for entry in entries:
        db_session.add(entry)
    await db_session.flush()
    return entries
