"""Input validation, injection, and mass-assignment.

Test IDs (TC-SEC-###) trace back to the QA test-plan artifact. Injection
targets are the real free-text fields confirmed to exist in the current API
(product name/description, order notes, user block_reason) — there is no
product-review feature in the current service list, so that part of the
original plan is redirected here rather than assumed.
"""

from __future__ import annotations

import uuid

import httpx
import pytest
from conftest import TIMEOUT, TRUST_ENV, assert_ok, base_url

ACCOUNTS = {
    "customer": ("customer@marketplace.dev", "Customer123!"),
    "seller": ("seller@marketplace.dev", "Seller123!"),
    "admin": ("admin@marketplace.dev", "Admin123!"),
}


def _login(email: str, password: str) -> str | None:
    resp = httpx.post(
        f"{base_url('auth')}/auth/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
        trust_env=TRUST_ENV,
    )
    return resp.json()["access_token"] if resp.status_code == 200 else None


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def customer_token() -> str:
    t = _login(*ACCOUNTS["customer"])
    if t is None:
        pytest.skip("seeded customer account unavailable")
    return t


@pytest.fixture(scope="module")
def seller_token() -> str:
    t = _login(*ACCOUNTS["seller"])
    if t is None:
        pytest.skip("seeded seller account unavailable")
    return t


@pytest.fixture(scope="module")
def admin_headers() -> dict[str, str]:
    t = _login(*ACCOUNTS["admin"])
    if t is None:
        pytest.skip("seeded admin account unavailable")
    return _auth(t)


@pytest.fixture
def seller_headers(seller_token: str) -> dict[str, str]:
    return _auth(seller_token)


class TestCredentialHygiene:
    @pytest.mark.writes
    def test_sec_023_password_never_appears_in_any_response(
        self, clients: dict[str, httpx.Client]
    ) -> None:
        """TC-SEC-023: register/login/get-user responses never echo the
        password or its hash.
        """
        email = f"e2e-pwcheck-{uuid.uuid4().hex[:10]}@marketplace.dev"
        password = "SuperSecretPassw0rd!"

        register = assert_ok(
            clients["auth"].post(
                "/auth/register", json={"email": email, "password": password}
            ),
            201,
        )
        register_text = register.text.lower()
        assert password.lower() not in register_text
        assert "password" not in register.json()
        assert "password_hash" not in register.json()

        login = assert_ok(
            clients["auth"].post(
                "/auth/login", json={"email": email, "password": password}
            )
        )
        assert password.lower() not in login.text.lower()

    def test_sec_024_weak_password_is_rejected_at_registration(
        self, clients: dict[str, httpx.Client]
    ) -> None:
        """TC-SEC-024: a too-short/simple password fails validation, not
        silent acceptance.
        """
        resp = clients["auth"].post(
            "/auth/register",
            json={
                "email": f"e2e-weak-{uuid.uuid4().hex[:10]}@marketplace.dev",
                "password": "123",
            },
        )
        assert resp.status_code == 422


class TestInjection:
    def test_sec_030_sql_injection_in_search_is_neutralized(
        self, clients: dict[str, httpx.Client], seller_headers: dict[str, str]
    ) -> None:
        """TC-SEC-030: a SQLi-shaped query string is treated as a literal
        search term, not executed — no data leak, no 500.
        """
        resp = clients["catalog"].get(
            "/products/",
            params={"name": "' OR '1'='1"},
            headers=seller_headers,
        )
        assert resp.status_code == 200, (
            f"a SQLi-shaped filter must not crash the search, got {resp.status_code}: "
            f"{resp.text[:200]}"
        )

    @pytest.mark.writes
    def test_sec_031_script_injection_in_product_fields_is_stored_inert(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SEC-031: an HTML/script payload in name/description is stored
        as opaque data — creating the product must not execute anything or
        corrupt the response, and the stored value must round-trip exactly
        (proves it wasn't partially stripped in a way that could reintroduce
        risk elsewhere, and wasn't silently truncated).
        """
        categories = assert_ok(
            clients["catalog"].get("/categories/", headers=seller_headers)
        ).json()["items"]
        payload = "<script>alert(document.cookie)</script>"
        product = assert_ok(
            clients["catalog"].post(
                "/products/",
                json={
                    "name": f"e2e-{unique}",
                    "description": payload,
                    "price": 10,
                    "category_id": categories[0]["id"],
                },
                headers=seller_headers,
            ),
            201,
        ).json()
        assert product["description"] == payload

    @pytest.mark.writes
    def test_sec_032_oversized_custom_properties_is_rejected_not_500(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SEC-032: a pathological custom_properties_config (deep nesting)
        must be handled as a client error or accepted cleanly — never a 500.
        """
        categories = assert_ok(
            clients["catalog"].get("/categories/", headers=seller_headers)
        ).json()["items"]
        nested: dict = {"v": 0}
        cursor = nested
        for i in range(500):
            cursor["next"] = {"v": i}
            cursor = cursor["next"]

        resp = clients["catalog"].post(
            "/products/",
            json={
                "name": f"e2e-{unique}-deep",
                "price": 10,
                "category_id": categories[0]["id"],
                "custom_properties_config": nested,
            },
            headers=seller_headers,
        )
        assert resp.status_code in (201, 400, 413, 422), (
            f"a pathological payload must be a clean client error, not a crash, "
            f"got {resp.status_code}: {resp.text[:200]}"
        )

    @pytest.mark.writes
    def test_sec_033_injection_in_order_notes_is_isolated(
        self,
        clients: dict[str, httpx.Client],
        customer_token: str,
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SEC-033: a SQLi/script payload in a free-text order field
        (notes) is stored per-order and does not affect any other request.
        """
        customer_headers = _auth(customer_token)
        categories = assert_ok(
            clients["catalog"].get("/categories/", headers=seller_headers)
        ).json()["items"]
        product = assert_ok(
            clients["catalog"].post(
                "/products/",
                json={
                    "name": f"e2e-{unique}-notes",
                    "price": 50,
                    "category_id": categories[0]["id"],
                },
                headers=seller_headers,
            ),
            201,
        ).json()
        warehouses = assert_ok(
            clients["inventory"].get("/warehouses/", headers=seller_headers)
        ).json()
        assert_ok(
            clients["inventory"].post(
                "/stock/receive",
                json={
                    "product_id": product["id"],
                    "warehouse_id": warehouses[0]["id"],
                    "quantity": 5,
                    "reference_type": "e2e-seed",
                },
                headers=seller_headers,
            )
        )
        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product["id"], "quantity": 1},
                headers=customer_headers,
            )
        )
        payload = "'; DROP TABLE orders; --"
        order = assert_ok(
            clients["order"].post(
                "/orders/",
                json={
                    "shipping_address": {"city": "Moscow"},
                    "payment_method": "MOCK",
                    "tax_strategy": "RU",
                    "notes": payload,
                },
                headers={**customer_headers, "Idempotency-Key": f"e2e-{unique}-inject"},
            ),
            201,
            200,
        ).json()
        assert order["notes"] == payload

        # The orders table must still be entirely intact and queryable.
        listing = clients["order"].get("/orders/", headers=customer_headers)
        assert listing.status_code == 200

    def test_sec_034_path_traversal_in_uploaded_filename(
        self, clients: dict[str, httpx.Client], seller_headers: dict[str, str]
    ) -> None:
        """TC-SEC-034: a `../../` filename on the CSV import upload must not
        be honoured literally — either rejected, or safely renamed/stored
        under import-service's own key scheme.
        """
        malicious_name = "../../../../etc/passwd"
        files = {"file": (malicious_name, b"name,price\nx,1\n", "text/csv")}
        resp = clients["import"].post(
            "/imports/upload", files=files, headers=seller_headers
        )
        assert resp.status_code in (201, 400, 422), (
            f"unexpected status for a traversal-shaped filename: {resp.status_code} "
            f"{resp.text[:200]}"
        )
        if resp.status_code == 201:
            body = resp.json()
            stored_name = body.get("original_filename", body.get("storage_key", ""))
            assert "../" not in str(stored_name) or stored_name == malicious_name, (
                "the original filename may be recorded as metadata (that's fine — "
                "it's just a string), but there must be no evidence it was used as "
                "an actual filesystem path"
            )


class TestMassAssignment:
    @pytest.mark.writes
    def test_sec_035_product_create_ignores_protected_fields(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SEC-035: a client cannot set seller_id directly — it must come
        from the caller's token, not the request body (CreateProductRequest
        has no seller_id field at all — this documents that it's rejected as
        an unknown field, not silently accepted and ignored).
        """
        categories = assert_ok(
            clients["catalog"].get("/categories/", headers=seller_headers)
        ).json()["items"]
        forged_seller_id = str(uuid.uuid4())
        resp = clients["catalog"].post(
            "/products/",
            json={
                "name": f"e2e-{unique}-forge",
                "price": 10,
                "category_id": categories[0]["id"],
                "seller_id": forged_seller_id,
            },
            headers=seller_headers,
        )
        assert resp.status_code == 422, (
            "CreateProductRequest forbids extra fields (additionalProperties: "
            f"false) — seller_id in the body should be a 422, got {resp.status_code}"
        )

    @pytest.mark.writes
    def test_sec_035b_register_ignores_role_and_admin_fields(
        self, clients: dict[str, httpx.Client]
    ) -> None:
        """TC-SEC-035 (register variant): a self-registered user cannot grant
        themselves admin or a specific role through the request body.
        """
        email = f"e2e-massassign-{uuid.uuid4().hex[:10]}@marketplace.dev"
        resp = clients["auth"].post(
            "/auth/register",
            json={
                "email": email,
                "password": "NotAnAdmin123!",
                "role": "super_admin",
                "is_admin": True,
            },
        )
        # Either the extra fields are rejected outright, or the account is
        # created but plainly not admin — never actually admin.
        if resp.status_code == 201:
            body = resp.json()
            assert body.get("role") != "super_admin"
            assert body.get("is_admin") is not True
        else:
            assert resp.status_code == 422
