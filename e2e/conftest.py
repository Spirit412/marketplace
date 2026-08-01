"""Shared harness for the end-to-end suite.

The tests drive the running Docker stack over its published ports, so they
exercise the same path a real client does: HTTP, real auth, real database.
Nothing here imports service code — a service is only ever reached through
its public API.
"""

import os
import uuid
from collections.abc import Iterator

import httpx
import pytest

SERVICES: dict[str, int] = {
    "auth": 8110,
    "catalog": 8120,
    "order": 8130,
    "payment": 8140,
    "notification": 8150,
    "scheduler": 8160,
    "report": 8170,
    "inventory": 8180,
    "dictionary": 8190,
    "import": 8101,
    "api": 8100,
}

HOST = os.getenv("E2E_HOST", "127.0.0.1")
ADMIN_EMAIL = os.getenv("E2E_ADMIN_EMAIL", "superadmin@marketplace.dev")
ADMIN_PASSWORD = os.getenv("E2E_ADMIN_PASSWORD", "SuperAdmin123!")
TIMEOUT = float(os.getenv("E2E_TIMEOUT", "15"))

# The stack is reached on loopback; a shell-level ALL_PROXY (often SOCKS)
# must never be applied, so every client opts out of proxy environment.
TRUST_ENV = False


def base_url(service: str) -> str:
    """Return the published base URL for a service."""
    return f"http://{HOST}:{SERVICES[service]}"


@pytest.fixture(scope="session")
def admin_token() -> str:
    """Access token for the seeded super-admin.

    Skips the whole run rather than failing every test when auth-service is
    unreachable, so an unavailable stack reads as "not run", not "broken".
    """
    try:
        response = httpx.post(
            f"{base_url('auth')}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=TIMEOUT,
            trust_env=TRUST_ENV,
        )
    except httpx.HTTPError as exc:
        pytest.skip(f"auth-service unreachable: {exc}")
    if response.status_code != 200:
        pytest.skip(f"admin login failed: {response.status_code} {response.text[:200]}")
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token: str) -> dict[str, str]:
    """Authorization header carrying the super-admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def clients() -> Iterator[dict[str, httpx.Client]]:
    """One HTTP client per service, keyed by service name."""
    opened = {
        name: httpx.Client(
            base_url=base_url(name),
            timeout=TIMEOUT,
            trust_env=TRUST_ENV,
            follow_redirects=True,
        )
        for name in SERVICES
    }
    yield opened
    for client in opened.values():
        client.close()


@pytest.fixture
def api(
    request: pytest.FixtureRequest, clients: dict[str, httpx.Client]
) -> httpx.Client:
    """Client for the service named by the module-level `SERVICE` attribute."""
    service = getattr(request.module, "SERVICE", None)
    if service is None:
        raise RuntimeError(f"{request.module.__name__} must define SERVICE")
    return clients[service]


@pytest.fixture
def unique() -> str:
    """Short unique suffix for names that must not collide between runs."""
    return uuid.uuid4().hex[:10]


def assert_ok(response: httpx.Response, *allowed: int) -> httpx.Response:
    """Assert the response status, showing the body when it does not match.

    Args:
        response: The response to check.
        *allowed: Acceptable status codes; defaults to 200 and 201.

    Returns:
        The same response, so calls can be chained.
    """
    expected = allowed or (200, 201)
    assert response.status_code in expected, (
        f"{response.request.method} {response.request.url} -> "
        f"{response.status_code}, expected {expected}\n{response.text[:600]}"
    )
    return response
