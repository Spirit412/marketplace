# E2E suite

End-to-end tests that drive the running Docker stack over its published ports.
Nothing here imports service code — each service is reached only through its
public HTTP API, so the tests exercise routing, auth, serialization and the
database the same way a real client does.

## Running

The stack must be up (`./manage.sh up` or `docker compose up -d`), and the RBAC
seed must have been applied so the super-admin exists.

```bash
cd e2e
python3 -m pytest -q                 # everything
python3 -m pytest -q -m "not writes" # read-only, leaves no data behind
python3 -m pytest -q tests/test_catalog.py
```

Tests marked `writes` create and remove their own records. They clean up after
themselves, but they do touch the live database.

## Layout

| File | Covers |
| --- | --- |
| `conftest.py` | Service registry, admin token, per-service HTTP clients, `assert_ok` |
| `tests/test_service_contract.py` | Rules every service obeys: health shape, OpenAPI, 401 on anonymous, 401 on a bad token, 404 on unknown routes |
| `tests/test_catalog.py` | catalog-service routers: categories, products, query sets |

`test_service_contract.py` discovers endpoints from each service's
`/openapi.json`, so a newly added route is covered by the auth checks without
touching the test. Endpoints that are public by design are listed explicitly in
`PUBLIC_PATHS` — a new anonymous route therefore has to be an intentional,
reviewable edit.

## Configuration

| Variable | Default |
| --- | --- |
| `E2E_HOST` | `127.0.0.1` |
| `E2E_ADMIN_EMAIL` | `superadmin@marketplace.dev` |
| `E2E_ADMIN_PASSWORD` | `SuperAdmin123!` |
| `E2E_TIMEOUT` | `15` |

Clients are created with `trust_env=False`: the stack is on loopback, and a
shell-level `ALL_PROXY` (often SOCKS) must never be applied to these calls.
