"""Test fixtures for import-service."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.datatype import uuid7
from src.enums.import_status import ImportStatus
from src.enums.import_type import ImportType
from src.models.import_row import ImportRow
from src.models.import_task import Base, ImportTask


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


@pytest.fixture
def temp_storage_dir() -> str:
    """Create temporary directory for file storage."""
    with TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest_asyncio.fixture
async def test_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP test client."""
    from src.main import app

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
async def seed_import_task(
    db_session: AsyncSession,
) -> ImportTask:
    """Seed a test import task."""
    task = ImportTask(
        id=uuid7(),
        seller_id=uuid7(),
        import_type=ImportType.PRODUCTS.value,
        file_name="test_products.csv",
        file_path="/tmp/test_products.csv",
        status=ImportStatus.PENDING.value,
    )
    db_session.add(task)
    await db_session.flush()
    return task
