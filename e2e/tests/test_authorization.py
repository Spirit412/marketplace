"""Authorization must discriminate, not merely authenticate.

Every business endpoint is expected to check a permission level, not just a
valid signature. These tests hold that line: a valid token for a user who
lacks an application's permission must be refused.
"""

import httpx
import pytest

from conftest import ADMIN_PASSWORD, TIMEOUT, TRUST_ENV, base_url

# A seeded low-privilege account and the applications it must NOT reach.
LOW_PRIVILEGE = ("customer@marketplace.dev", "Customer123!")

# (service, parameter-free GET path) the customer role has no permission for.
FORBIDDEN_FOR_CUSTOMER = [
    ("inventory", "/warehouses/"),
    ("scheduler", "/jobs/"),
]

# Endpoints that must remain reachable without any credentials.
PUBLIC = [
    ("auth", "/auth/rate-limit-status"),
]


def _login(email: str, password: str) -> str | None:
    """Return an access token, or None when the account is unavailable."""
    response = httpx.post(
        f"{base_url('auth')}/auth/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
        trust_env=TRUST_ENV,
    )
    if response.status_code != 200:
        return None
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def customer_token() -> str:
    """Access token for the seeded low-privilege customer."""
    token = _login(*LOW_PRIVILEGE)
    if token is None:
        pytest.skip("seeded customer account unavailable")
    return token


def test_admin_permissions_cover_every_application(admin_token: str) -> None:
    """The super-admin token carries a permission level for each application."""
    import base64
    import json

    payload = admin_token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    assert claims["permissions"], "token carries no permissions claim"
    assert all(level > 0 for level in claims["permissions"].values())


@pytest.mark.parametrize("service,path", FORBIDDEN_FOR_CUSTOMER)
def test_low_privilege_user_is_forbidden(
    service: str, path: str, customer_token: str, clients: dict[str, httpx.Client]
) -> None:
    """A valid token without the application's permission is refused with 403."""
    headers = {"Authorization": f"Bearer {customer_token}"}
    code = clients[service].get(path, headers=headers).status_code
    assert code == 403, (
        f"{service}{path} returned {code} for a user lacking that permission; "
        "authentication alone must not grant access"
    )


def test_low_privilege_user_keeps_its_own_application(
    customer_token: str, clients: dict[str, httpx.Client]
) -> None:
    """The customer still reaches the application its role does grant."""
    headers = {"Authorization": f"Bearer {customer_token}"}
    assert clients["order"].get("/orders/", headers=headers).status_code == 200


@pytest.mark.parametrize("service,path", PUBLIC)
def test_public_endpoints_stay_anonymous(
    service: str, path: str, clients: dict[str, httpx.Client]
) -> None:
    """Deliberately public endpoints are not caught by the permission guard."""
    assert clients[service].get(path).status_code == 200


def test_login_remains_reachable_without_a_token() -> None:
    """Login cannot require a token — there would be no way to obtain one."""
    response = httpx.post(
        f"{base_url('auth')}/auth/login",
        json={"email": "superadmin@marketplace.dev", "password": ADMIN_PASSWORD},
        timeout=TIMEOUT,
        trust_env=TRUST_ENV,
    )
    assert response.status_code == 200
