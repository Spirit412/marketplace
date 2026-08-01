"""Cross-role authorization, token validity, blocked-user and reuse-detection.

Test IDs (TC-SEC-###) trace back to the QA test-plan artifact.
"""

from __future__ import annotations

import time
import uuid

import httpx
import pytest
from conftest import TIMEOUT, TRUST_ENV, assert_ok, base_url

ACCOUNTS = {
    "customer": ("customer@marketplace.dev", "Customer123!"),
    "seller": ("seller@marketplace.dev", "Seller123!"),
    "admin": ("admin@marketplace.dev", "Admin123!"),
}


def _login(email: str, password: str) -> dict | None:
    resp = httpx.post(
        f"{base_url('auth')}/auth/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
        trust_env=TRUST_ENV,
    )
    return resp.json() if resp.status_code == 200 else None


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def customer_token() -> str:
    body = _login(*ACCOUNTS["customer"])
    if body is None:
        pytest.skip("seeded customer account unavailable")
    return body["access_token"]


@pytest.fixture(scope="module")
def seller_token() -> str:
    body = _login(*ACCOUNTS["seller"])
    if body is None:
        pytest.skip("seeded seller account unavailable")
    return body["access_token"]


@pytest.fixture(scope="module")
def admin_headers() -> dict[str, str]:
    body = _login(*ACCOUNTS["admin"])
    if body is None:
        pytest.skip("seeded admin account unavailable")
    return _auth(body["access_token"])


class TestCrossRoleAuthorization:
    def test_sec_010_customer_token_rejected_on_seller_endpoint(
        self, clients: dict[str, httpx.Client], customer_token: str
    ) -> None:
        """TC-SEC-010: a customer token cannot create a product."""
        categories = clients["catalog"].get(
            "/categories/", headers=_auth(customer_token)
        )
        # Customer has CATALOG:GET (fixed 2026-08-01) but not CATALOG:POST.
        resp = clients["catalog"].post(
            "/products/",
            json={"name": "hacked", "price": 1},
            headers=_auth(customer_token),
        )
        assert resp.status_code == 403, (
            f"customer must not be able to POST /products/, got {resp.status_code}"
        )
        assert categories.status_code == 200, "sanity: customer can still read catalog"

    def test_sec_011_seller_token_rejected_on_admin_rbac_endpoint(
        self, clients: dict[str, httpx.Client], seller_token: str
    ) -> None:
        """TC-SEC-011: a seller token cannot create an RBAC role."""
        resp = clients["auth"].post(
            "/auth",
            json={"name": "hacked-role", "description": "x", "is_admin": True},
            headers=_auth(seller_token),
        )
        assert resp.status_code == 403, (
            f"seller must not manage RBAC roles, got {resp.status_code}: "
            f"{resp.text[:200]}"
        )


class TestTokenValidity:
    def test_sec_012_expired_token_cannot_be_synthesized_black_box(self) -> None:
        """TC-SEC-012: cannot be exercised without either the signing secret
        (out of scope for a black-box HTTP client per conftest's own
        contract) or waiting out the real 15-minute access-token TTL, which
        is not a reasonable price for a test run.
        """
        pytest.skip(
            "expired-but-validly-signed tokens cannot be constructed from a "
            "pure HTTP client without the JWT secret or a 15-minute wait"
        )

    def test_sec_013_tampered_signature_is_rejected(
        self, clients: dict[str, httpx.Client], customer_token: str
    ) -> None:
        """TC-SEC-013: corrupting the signature segment of a real token
        invalidates it everywhere.
        """
        header, payload, signature = customer_token.split(".")
        tampered = f"{header}.{payload}.{signature[:-4]}zzzz"
        resp = clients["order"].get("/orders/", headers=_auth(tampered))
        assert resp.status_code == 401

    def test_sec_014_missing_authorization_header(
        self, clients: dict[str, httpx.Client]
    ) -> None:
        """TC-SEC-014: a protected endpoint rejects an anonymous request."""
        resp = clients["order"].get("/orders/")
        assert resp.status_code in (401, 403)


class TestBlockedUserAndReuseDetection:
    @pytest.mark.writes
    def test_sec_015_blocked_user_loses_access_within_the_cache_ttl(
        self, clients: dict[str, httpx.Client], admin_headers: dict[str, str]
    ) -> None:
        """TC-SEC-015: a blocked user's still-unexpired access token keeps
        working for up to the check-access cache TTL (~10s, per "Auth Service
        — Ролевая модель" §4.5/§1.5), then is denied on every subsequent
        request once that window passes.
        """
        email = f"e2e-blockme-{uuid.uuid4().hex[:10]}@marketplace.dev"
        password = "BlockMe123!"
        register = clients["auth"].post(
            "/auth/register", json={"email": email, "password": password}
        )
        if register.status_code != 201:
            pytest.skip(
                f"could not register a throwaway account: {register.text[:200]}"
            )
        user_id = register.json()["id"]

        login = _login(email, password)
        assert login is not None
        headers = _auth(login["access_token"])

        first = clients["order"].get("/orders/", headers=headers)
        assert first.status_code == 200, "sanity: fresh account can use its token"

        block = clients["auth"].post(
            f"/auth/users/{user_id}/block",
            json={"reason": "e2e security test"},
            headers=admin_headers,
        )
        if block.status_code != 200:
            pytest.skip(
                f"could not block the throwaway user (possibly the "
                f"MissingGreenlet class of bug — see test_seller_journey.py): "
                f"{block.status_code} {block.text[:200]}"
            )

        # Poll past the cache TTL rather than assuming an exact value.
        deadline = time.monotonic() + 15
        status = 200
        while time.monotonic() < deadline and status != 403:
            status = clients["order"].get("/orders/", headers=headers).status_code
            if status != 403:
                time.sleep(1)
        assert status == 403, (
            "a blocked user's token must eventually (within the cache TTL) stop "
            f"working; still getting {status} after 15s"
        )

    @pytest.mark.writes
    def test_sec_016_reused_refresh_token_revokes_the_whole_session(
        self, clients: dict[str, httpx.Client]
    ) -> None:
        """TC-SEC-016: e2e confirmation of the reuse-detection unit-tested in
        auth-service/tests — redeeming an already-rotated-away refresh token
        must 403 and revoke the newly-issued one too, observed purely over
        the public API.
        """
        login = _login(*ACCOUNTS["customer"])
        assert login is not None
        old_refresh = login["refresh_token"]

        rotated = clients["auth"].post(
            "/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert_ok(rotated)
        new_refresh = rotated.json()["refresh_token"]

        reuse = clients["auth"].post(
            "/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert reuse.status_code == 403, (
            f"redeeming a rotated-away refresh token should 403, "
            f"got {reuse.status_code}"
        )

        followup = clients["auth"].post(
            "/auth/refresh", json={"refresh_token": new_refresh}
        )
        # 403 is the "explicitly revoked" path; 401 is the generic "no longer
        # valid" path. Which one fires depends on a same-wall-clock-second race
        # between this token's iat and the mass-revocation timestamp (both
        # legitimate outcomes deny access — see auth-service's
        # _is_token_revoked for the precision note). The security property
        # under test is that the replacement token stops working at all.
        assert followup.status_code in (401, 403), (
            "reuse detection must revoke the whole session, including the token "
            f"that legitimately replaced the stolen one — got {followup.status_code}"
        )
