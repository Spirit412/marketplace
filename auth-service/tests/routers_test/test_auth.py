"""Integration tests for /auth endpoints — register, login, logout, permissions."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_EMAIL_PREFIX

REGISTER_EMAIL = f"{TEST_EMAIL_PREFIX}register@marketplace.dev"
LOGIN_EMAIL = f"{TEST_EMAIL_PREFIX}login@marketplace.dev"
LOGOUT_EMAIL = f"{TEST_EMAIL_PREFIX}logout@marketplace.dev"
LOGOUT_ALL_EMAIL = f"{TEST_EMAIL_PREFIX}logoutall@marketplace.dev"
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
        assert refresh_resp.status_code == 403
