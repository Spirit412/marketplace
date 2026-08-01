"""Tests for the shared AuthMiddleware (src/auth_middleware.py).

This file is copied byte-identical into all 10 services (see "Auth Service —
Ролевая модель" §4.4/4.5 in the docs) — auth-service itself never mounts it
(it authorizes its own routes directly), so it has no other test coverage.
Testing the one canonical copy here covers the check-access caching and
Redis-outage fallback behaviour used by every service that mounts it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport
from httpx import AsyncClient as HttpxAsyncClient

from src import auth_middleware
from src.auth_middleware import AuthMiddleware, _cache_key, init_auth
from src.config.settings import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

TEST_APP_ID = "TESTAPP"


def _build_app() -> FastAPI:
    app = FastAPI()

    @app.get("/items")
    async def get_items() -> dict[str, bool]:
        return {"ok": True}

    app.add_middleware(AuthMiddleware, exclude_paths=["/health"])
    return app


def _fake_auth_response(payload: dict[str, Any]) -> MagicMock:
    """A stand-in for httpx.Response good enough for AuthMiddleware's needs.

    .raise_for_status() (no-op) and .json() (returns the given payload).
    """
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=payload)
    return resp


async def _clear_cache_entry(token: str, method: str, path: str) -> None:
    """Delete exactly the one cache key a test is about to exercise.

    Deliberately not a blanket flush — this Redis is the shared dev instance
    other running services may be using at the same time.

    Reads `auth_middleware._REDIS` through the module object rather than a
    plain top-level `from ... import _REDIS`, since `init_auth()` reassigns
    that module-level global after this test module is imported — a name
    copied at import time would stay bound to the pre-init `None`.
    """
    if auth_middleware._REDIS is not None:
        await auth_middleware._REDIS.delete(_cache_key(token, method, path))


@pytest.fixture
async def middleware_client() -> AsyncGenerator[HttpxAsyncClient, None]:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with HttpxAsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestCheckAccessCache:
    @pytest.mark.asyncio
    async def test_second_identical_request_is_served_from_cache(
        self, middleware_client: HttpxAsyncClient
    ) -> None:
        init_auth(
            auth_service_url="http://fake-auth",
            app_id=TEST_APP_ID,
            redis_url=settings.redis.url,
            cache_ttl_seconds=5,
        )
        await _clear_cache_entry("sometoken", "GET", "/items")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _fake_auth_response(
                {
                    "allowed": True,
                    "user_id": "u1",
                    "role": "customer",
                    "is_admin": False,
                }
            )
            headers = {"Authorization": "Bearer sometoken"}

            first = await middleware_client.get("/items", headers=headers)
            second = await middleware_client.get("/items", headers=headers)

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert mock_post.call_count == 1, (
            "second identical request should be served from cache, "
            "not hit auth-service again"
        )

    @pytest.mark.asyncio
    async def test_denied_decision_is_cached_too(
        self, middleware_client: HttpxAsyncClient
    ) -> None:
        init_auth(
            auth_service_url="http://fake-auth",
            app_id=TEST_APP_ID,
            redis_url=settings.redis.url,
            cache_ttl_seconds=5,
        )
        await _clear_cache_entry("deniedtoken", "GET", "/items")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _fake_auth_response(
                {
                    "allowed": False,
                    "user_id": "u1",
                    "role": "customer",
                    "is_admin": False,
                }
            )
            headers = {"Authorization": "Bearer deniedtoken"}

            first = await middleware_client.get("/items", headers=headers)
            second = await middleware_client.get("/items", headers=headers)

        assert first.status_code == 403
        assert second.status_code == 403
        assert mock_post.call_count == 1

    @pytest.mark.asyncio
    async def test_different_tokens_do_not_share_a_cache_entry(
        self, middleware_client: HttpxAsyncClient
    ) -> None:
        init_auth(
            auth_service_url="http://fake-auth",
            app_id=TEST_APP_ID,
            redis_url=settings.redis.url,
            cache_ttl_seconds=5,
        )
        await _clear_cache_entry("tokenA", "GET", "/items")
        await _clear_cache_entry("tokenB", "GET", "/items")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = _fake_auth_response(
                {
                    "allowed": True,
                    "user_id": "u1",
                    "role": "customer",
                    "is_admin": False,
                }
            )
            await middleware_client.get(
                "/items", headers={"Authorization": "Bearer tokenA"}
            )
            await middleware_client.get(
                "/items", headers={"Authorization": "Bearer tokenB"}
            )

        assert mock_post.call_count == 2, (
            "different tokens must not share a cache entry"
        )

    @pytest.mark.asyncio
    async def test_redis_outage_falls_back_to_auth_service_every_time(
        self, middleware_client: HttpxAsyncClient
    ) -> None:
        """Cache infrastructure failing must degrade to the old behaviour.

        It must not break requests or bypass the authorization decision.
        """
        init_auth(
            auth_service_url="http://fake-auth",
            app_id=TEST_APP_ID,
            redis_url="redis://localhost:1",  # nothing listens here
            cache_ttl_seconds=5,
        )
        try:
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = _fake_auth_response(
                    {
                        "allowed": True,
                        "user_id": "u1",
                        "role": "customer",
                        "is_admin": False,
                    }
                )
                headers = {"Authorization": "Bearer sometoken"}

                first = await middleware_client.get("/items", headers=headers)
                second = await middleware_client.get("/items", headers=headers)

            assert first.status_code == 200
            assert second.status_code == 200
            assert mock_post.call_count == 2, (
                "no working cache — every request must hit auth-service"
            )
        finally:
            # Leave the module in a working state for any test that runs after this one.
            init_auth(
                auth_service_url="http://fake-auth",
                app_id=TEST_APP_ID,
                redis_url=settings.redis.url,
                cache_ttl_seconds=5,
            )
