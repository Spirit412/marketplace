"""Contract every service must satisfy, regardless of its domain."""

import httpx
import pytest
from conftest import SERVICES, TIMEOUT, TRUST_ENV, assert_ok, base_url

ALL_SERVICES = sorted(SERVICES)

# Endpoints that are anonymous by design. Anything not listed here must
# reject unauthenticated callers, so a new public route is a deliberate,
# reviewable edit rather than an accident.
PUBLIC_PATHS: dict[str, set[str]] = {
    "auth": {"/auth/rate-limit-status"},
}


@pytest.mark.parametrize("service", ALL_SERVICES)
def test_health_is_reachable(service: str, clients: dict[str, httpx.Client]) -> None:
    """Every service exposes /health without authentication."""
    body = assert_ok(clients[service].get("/health")).json()
    assert body["status"] in {"healthy", "degraded"}, body
    assert "checks" in body


@pytest.mark.parametrize("service", ALL_SERVICES)
def test_health_reports_its_own_name(
    service: str, clients: dict[str, httpx.Client]
) -> None:
    """The health payload identifies which service answered."""
    body = clients[service].get("/health").json()
    assert body.get("service", "").startswith(service), body


@pytest.mark.parametrize("service", ALL_SERVICES)
def test_openapi_schema_is_served(
    service: str, clients: dict[str, httpx.Client]
) -> None:
    """The OpenAPI document is served and declares at least one path."""
    schema = assert_ok(clients[service].get("/openapi.json")).json()
    assert schema["paths"], f"{service} declares no paths"


@pytest.mark.parametrize("service", ALL_SERVICES)
def test_unknown_route_is_404(service: str, clients: dict[str, httpx.Client]) -> None:
    """An unmapped path is a 404, never a crash."""
    response = clients[service].get("/e2e-no-such-route")
    assert response.status_code in (401, 404), response.status_code


def _protected_get_paths(service: str) -> list[str]:
    """Parameter-free GET paths that should require authentication."""
    schema = httpx.get(
        f"{base_url(service)}/openapi.json", timeout=TIMEOUT, trust_env=TRUST_ENV
    ).json()
    public = PUBLIC_PATHS.get(service, set())
    return [
        path
        for path, ops in schema["paths"].items()
        if "get" in ops
        and "{" not in path
        and not path.startswith("/health")
        and path not in public
    ]


@pytest.mark.parametrize("service", ALL_SERVICES)
def test_protected_endpoints_reject_anonymous(
    service: str, clients: dict[str, httpx.Client]
) -> None:
    """Business endpoints refuse unauthenticated callers.

    A service with no parameter-free GET routes has nothing to assert here,
    so it is skipped rather than silently passing.
    """
    paths = [p for p in _protected_get_paths(service) if p != "/openapi.json"]
    if not paths:
        pytest.skip(f"{service} exposes no parameter-free GET routes")
    unauthorised = []
    for path in paths:
        code = clients[service].get(path).status_code
        if code not in (401, 403):
            unauthorised.append((path, code))
    assert not unauthorised, f"{service} allows anonymous access: {unauthorised}"


@pytest.mark.parametrize("service", ALL_SERVICES)
def test_garbage_token_is_rejected(
    service: str, clients: dict[str, httpx.Client]
) -> None:
    """A malformed bearer token is rejected with 401, not a 500."""
    paths = [p for p in _protected_get_paths(service) if p != "/openapi.json"]
    if not paths:
        pytest.skip(f"{service} exposes no parameter-free GET routes")
    headers = {"Authorization": "Bearer not.a.real.token"}
    code = clients[service].get(paths[0], headers=headers).status_code
    assert code == 401, f"{service} {paths[0]} -> {code}, expected 401"
