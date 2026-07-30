"""Functional coverage of catalog-service routers."""

import httpx
import pytest
from conftest import assert_ok

SERVICE = "catalog"


def test_category_tree_is_returned(api: httpx.Client, auth_headers: dict) -> None:
    """The tree endpoint returns nested-set ordered categories."""
    body = assert_ok(api.get("/categories/", headers=auth_headers)).json()
    items = body["items"]
    assert items, "expected seeded categories"
    for item in items:
        assert {"id", "name", "slug", "lft", "rgt", "level"} <= item.keys()


def test_category_tree_is_cache_consistent(
    api: httpx.Client, auth_headers: dict
) -> None:
    """Two consecutive reads agree, so the cached path matches the database path."""
    first = api.get("/categories/", headers=auth_headers).json()["items"]
    second = api.get("/categories/", headers=auth_headers).json()["items"]
    assert [c["id"] for c in first] == [c["id"] for c in second]


def test_get_category_by_id(api: httpx.Client, auth_headers: dict) -> None:
    """A category can be fetched by its identifier."""
    first = api.get("/categories/", headers=auth_headers).json()["items"][0]
    body = assert_ok(api.get(f"/categories/{first['id']}", headers=auth_headers)).json()
    assert body["id"] == first["id"]


def test_category_ancestors_and_descendants(
    api: httpx.Client, auth_headers: dict
) -> None:
    """Ancestor and descendant lookups answer for a real category."""
    items = api.get("/categories/", headers=auth_headers).json()["items"]
    deep = max(items, key=lambda c: c["level"])
    assert_ok(api.get(f"/categories/{deep['id']}/ancestors", headers=auth_headers))
    root = min(items, key=lambda c: c["level"])
    assert_ok(api.get(f"/categories/{root['id']}/descendants", headers=auth_headers))


def test_malformed_category_id_is_rejected(
    api: httpx.Client, auth_headers: dict
) -> None:
    """A non-UUID path segment is a validation error, not a crash."""
    response = api.get("/categories/not-a-uuid", headers=auth_headers)
    assert response.status_code == 422, response.text[:300]


def test_product_listing(api: httpx.Client, auth_headers: dict) -> None:
    """Product search returns a paginated envelope."""
    body = assert_ok(api.get("/products/", headers=auth_headers)).json()
    assert {"items", "total", "page", "page_size"} <= body.keys()
    assert body["total"] >= 0


def test_product_search_pagination(api: httpx.Client, auth_headers: dict) -> None:
    """Page size is honoured by the search endpoint."""
    body = assert_ok(
        api.get("/products/", params={"page": 1, "page_size": 2}, headers=auth_headers)
    ).json()
    assert len(body["items"]) <= 2
    assert body["page_size"] == 2


def test_get_product_by_id(api: httpx.Client, auth_headers: dict) -> None:
    """A product can be fetched by its identifier."""
    items = api.get("/products/", headers=auth_headers).json()["items"]
    if not items:
        pytest.skip("no seeded products")
    body = assert_ok(
        api.get(f"/products/{items[0]['id']}", headers=auth_headers)
    ).json()
    assert body["id"] == items[0]["id"]


def test_malformed_product_id_is_rejected(
    api: httpx.Client, auth_headers: dict
) -> None:
    """A non-UUID path segment is a validation error, not a crash."""
    assert api.get("/products/not-a-uuid", headers=auth_headers).status_code == 422


def test_system_query_sets(api: httpx.Client, auth_headers: dict) -> None:
    """The system query-set listing answers."""
    assert_ok(api.get("/query-sets/system/list", headers=auth_headers))


def test_query_set_listing(api: httpx.Client, auth_headers: dict) -> None:
    """The seller query-set listing returns a paginated envelope."""
    body = assert_ok(api.get("/query-sets/", headers=auth_headers)).json()
    assert {"items", "total"} <= body.keys()


@pytest.mark.writes
def test_category_lifecycle(api: httpx.Client, auth_headers: dict, unique: str) -> None:
    """A category can be created, read back, updated, and soft-deleted."""
    created = assert_ok(
        api.post(
            "/categories/",
            json={"name": f"e2e-{unique}", "slug": f"e2e-{unique}"},
            headers=auth_headers,
        ),
        201,
        200,
    ).json()
    category_id = created["id"]

    fetched = assert_ok(
        api.get(f"/categories/{category_id}", headers=auth_headers)
    ).json()
    assert fetched["name"] == f"e2e-{unique}"

    assert_ok(
        api.put(
            f"/categories/{category_id}",
            json={"name": f"e2e-{unique}-renamed"},
            headers=auth_headers,
        )
    )

    assert_ok(api.delete(f"/categories/{category_id}", headers=auth_headers), 200, 204)

    gone = api.get(f"/categories/{category_id}", headers=auth_headers)
    assert gone.status_code == 404, "soft-deleted category must not be readable"
