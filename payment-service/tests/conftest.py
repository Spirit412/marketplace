"""Test fixtures for payment-service."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.main import app
from src.models.payment import Base


@pytest.fixture
async def test_engine():
    """In-memory SQLite engine for tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """In-memory SQLite session."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def test_redis(mocker):
    """Mocked Redis client."""
    mock = mocker.MagicMock()
    mock.setnx.return_value = True
    mock.expire.return_value = True
    mock.get.return_value = None
    mock.ping.return_value = True
    return mock


@pytest.fixture
async def test_app() -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers() -> dict:
    """Mock JWT auth headers."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_gateway():
    """Mock gateway instance."""
    from src.services.gateway_strategy import MockGateway

    return MockGateway()
