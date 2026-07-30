"""Test fixtures for order-service."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.config.settings import get_settings
from src.main import app as fastapi_app


@pytest.fixture
def test_app():
    """Return the FastAPI app (override deps at test time)."""
    return fastapi_app


@pytest.fixture
async def async_client(
    test_app,
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for integration tests."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Mock JWT auth headers."""
    return {
        "Authorization": "Bearer test-token",
    }


@pytest.fixture
def mock_redis() -> MagicMock:
    """Mock Redis client."""
    redis = MagicMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.hincrby = AsyncMock()
    redis.hdel = AsyncMock()
    redis.delete = AsyncMock()
    redis.expire = AsyncMock()
    redis.hlen = AsyncMock(return_value=0)
    redis.setnx = AsyncMock(return_value=True)
    redis.ping = AsyncMock(return_value=True)
    redis.aclose = AsyncMock()
    return redis


@pytest.fixture
def mock_inventory_client() -> MagicMock:
    """Mock InventoryClient."""
    client = MagicMock()
    client.check_stock = AsyncMock(return_value=True)
    client.reserve = AsyncMock(return_value={"reserved": True})
    client.release = AsyncMock(return_value={"released": True})
    return client


@pytest.fixture
def mock_token_payload() -> MagicMock:
    """Mock token payload."""
    payload = MagicMock()
    payload.user_uuid = "11111111-1111-1111-1111-111111111111"
    payload.type = "access"
    return payload
