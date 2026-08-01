"""Integration tests for /auth endpoints — register, login, logout, permissions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.config.settings import settings
from src.engines.redis_client import get_redis_client
from tests.conftest import TEST_EMAIL_PREFIX

if TYPE_CHECKING:
    from httpx import AsyncClient

REGISTER_EMAIL = f"{TEST_EMAIL_PREFIX}register@marketplace.dev"
LOGIN_EMAIL = f"{TEST_EMAIL_PREFIX}login@marketplace.dev"
LOGOUT_EMAIL = f"{TEST_EMAIL_PREFIX}logout@marketplace.dev"
LOGOUT_ALL_EMAIL = f"{TEST_EMAIL_PREFIX}logoutall@marketplace.dev"
RATE_LIMIT_EMAIL = f"{TEST_EMAIL_PREFIX}ratelimit@marketplace.dev"
REUSE_EMAIL = f"{TEST_EMAIL_PREFIX}reuse@marketplace.dev"
PASSWORD = "TestPassw0rd!"


async def _register_and_login(client: AsyncClient, email: str) -> tuple[str, str]:
    """Register a fresh user then log in. Returns (access_token, refresh_token)."""
    register_resp = await client.post(
        "/auth/register", json={"email": email, "password": PASSWORD}
    )
    assert register_resp.status_code == 201, register_resp.text

    login_resp = await client.post(
        "/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert login_resp.status_code == 200, login_resp.text
    body = login_resp.json()
    return body["access_token"], body["refresh_token"]


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_creates_user_with_customer_role(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.post(
            "/auth/register",
            json={"email": REGISTER_EMAIL, "password": PASSWORD},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["email"] == REGISTER_EMAIL
        assert body["is_blocked"] is False
        assert body["role"] == "customer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_is_conflict(
        self, async_client: AsyncClient
    ) -> None:
        first = await async_client.post(
            "/auth/register",
            json={"email": REGISTER_EMAIL, "password": PASSWORD},
        )
        assert first.status_code == 201, first.text

        second = await async_client.post(
            "/auth/register",
            json={"email": REGISTER_EMAIL, "password": PASSWORD},
        )
        assert second.status_code == 409

    @pytest.mark.asyncio
    async def test_register_rejects_short_password(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.post(
            "/auth/register",
            json={"email": REGISTER_EMAIL, "password": "short"},
        )
        assert response.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_with_correct_password_returns_tokens(
        self, async_client: AsyncClient
    ) -> None:
        await async_client.post(
            "/auth/register", json={"email": LOGIN_EMAIL, "password": PASSWORD}
        )

        response = await async_client.post(
            "/auth/login", json={"email": LOGIN_EMAIL, "password": PASSWORD}
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_wrong_password_is_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        await async_client.post(
            "/auth/register", json={"email": LOGIN_EMAIL, "password": PASSWORD}
        )

        response = await async_client.post(
            "/auth/login", json={"email": LOGIN_EMAIL, "password": "WrongPassword1!"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_unknown_email_is_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.post(
            "/auth/login",
            json={
                "email": f"{TEST_EMAIL_PREFIX}never-registered@marketplace.dev",
                "password": PASSWORD,
            },
        )
        assert response.status_code == 401


class TestProtectedEndpoints:
    @pytest.mark.asyncio
    async def test_sessions_without_token_is_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.get("/auth/sessions")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_check_credentials_with_valid_token(
        self, async_client: AsyncClient
    ) -> None:
        access_token, _ = await _register_and_login(async_client, LOGIN_EMAIL)

        response = await async_client.post(
            "/auth/check_credentials",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["valid"] is True
        assert body["role"] == "customer"
        assert body["is_admin"] is False

    @pytest.mark.asyncio
    async def test_check_credentials_with_garbage_token_is_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        response = await async_client.post(
            "/auth/check_credentials",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_block_user_requires_admin(self, async_client: AsyncClient) -> None:
        access_token, _ = await _register_and_login(async_client, LOGIN_EMAIL)

        response = await async_client.post(
            "/auth/users/00000000-0000-0000-0000-000000000000/block",
            json={"reason": "test"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_revokes_refresh_token(
        self, async_client: AsyncClient
    ) -> None:
        _, refresh_token = await _register_and_login(async_client, LOGOUT_EMAIL)

        logout_resp = await async_client.post(
            "/auth/logout", json={"refresh_token": refresh_token}
        )
        assert logout_resp.status_code == 204

        refresh_resp = await async_client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert refresh_resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_all_revokes_all_sessions(
        self, async_client: AsyncClient
    ) -> None:
        access_token, refresh_token = await _register_and_login(
            async_client, LOGOUT_ALL_EMAIL
        )

        response = await async_client.post(
            "/auth/logout-all",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 204

        refresh_resp = await async_client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        # 403 is the "explicitly revoked" path (_is_token_revoked); 401 is the
        # generic "no longer valid" path. Which one fires depends on a
        # same-wall-clock-second race between this token's iat and the
        # logout-all timestamp (see _is_token_revoked's precision note) — both
        # correctly deny access, which is the property under test.
        assert refresh_resp.status_code in (401, 403)


class TestLoginRateLimit:
    @pytest.mark.asyncio
    async def test_login_is_throttled_after_threshold(
        self, async_client: AsyncClient
    ) -> None:
        """POST /auth/login must 429 once RATE_LIMIT_MAX_REQUESTS is hit for an IP.

        Regression test for the rate limiter that used to be declared in
        settings but never actually enforced (RATE_LIMIT_MAX_REQUESTS /
        RATE_LIMIT_WINDOW_SECONDS existed, GET /auth/rate-limit-status read a
        counter nothing ever incremented).
        """
        redis_client = get_redis_client()
        status_before = (await async_client.get("/auth/rate-limit-status")).json()
        ip = status_before["ip"]
        key = f"{settings.REDIS_KEY_PREFIX}:rate_limit:{ip}"

        try:
            remaining = (
                settings.RATE_LIMIT_MAX_REQUESTS - status_before["current_count"]
            )
            for _ in range(max(remaining, 0)):
                await async_client.post(
                    "/auth/login",
                    json={
                        "email": RATE_LIMIT_EMAIL,
                        "password": "whatever-not-matched",
                    },
                )

            blocked = await async_client.post(
                "/auth/login",
                json={"email": RATE_LIMIT_EMAIL, "password": "whatever-not-matched"},
            )
            assert blocked.status_code == 429, blocked.text
        finally:
            # Don't leave the shared dev IP counter poisoned for 60s after the test.
            await redis_client.delete(key)


class TestRefreshReuseDetection:
    @pytest.mark.asyncio
    async def test_reusing_a_rotated_refresh_token_revokes_the_whole_session(
        self, async_client: AsyncClient
    ) -> None:
        """Redeeming an already-rotated-away refresh token is a theft signal.

        It must 403 (not the plain 401 given to any other invalid token) and
        revoke every other active session for the user — including the token
        that legitimately replaced the stolen one.
        """
        _, refresh_token = await _register_and_login(async_client, REUSE_EMAIL)

        rotate_resp = await async_client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert rotate_resp.status_code == 200, rotate_resp.text
        new_refresh_token = rotate_resp.json()["refresh_token"]

        reuse_resp = await async_client.post(
            "/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert reuse_resp.status_code == 403, reuse_resp.text

        followup_resp = await async_client.post(
            "/auth/refresh", json={"refresh_token": new_refresh_token}
        )
        # See the comment on test_logout_all_revokes_all_sessions — same
        # same-second precision tradeoff applies to the replacement token.
        assert followup_resp.status_code in (401, 403), followup_resp.text

    @pytest.mark.asyncio
    async def test_unknown_refresh_token_is_plain_unauthorized(
        self, async_client: AsyncClient
    ) -> None:
        """A token that was never issued/rotated is just invalid.

        No reuse signal, no mass logout.
        """
        response = await async_client.post(
            "/auth/refresh", json={"refresh_token": "not-a-real-token"}
        )
        assert response.status_code == 401
