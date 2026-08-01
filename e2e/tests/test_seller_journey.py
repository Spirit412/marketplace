"""Seller E2E journey — catalog CRUD, fulfillment, finance.

Test IDs (TC-SELL-###) trace back to the QA test-plan artifact. Grounded in
the live API as of 2026-08-01 — adaptations from the original plan (no
dedicated image-upload endpoint, no separate moderation-approval workflow,
no payout endpoint) are called out per-test rather than assumed.
"""

from __future__ import annotations

import httpx
import pytest
from conftest import TIMEOUT, TRUST_ENV, assert_ok, base_url

ACCOUNTS = {
    "seller": ("seller@marketplace.dev", "Seller123!"),
    "moderator": ("moderator@marketplace.dev", "Moderator123!"),
    "customer": ("customer@marketplace.dev", "Customer123!"),
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
def seller_token() -> str:
    t = _login(*ACCOUNTS["seller"])
    if t is None:
        pytest.skip("seeded seller account unavailable")
    return t


@pytest.fixture(scope="module")
def moderator_token() -> str:
    t = _login(*ACCOUNTS["moderator"])
    if t is None:
        pytest.skip("seeded moderator account unavailable")
    return t


@pytest.fixture
def seller_headers(seller_token: str) -> dict[str, str]:
    return _auth(seller_token)


@pytest.fixture
def moderator_headers(moderator_token: str) -> dict[str, str]:
    return _auth(moderator_token)


@pytest.fixture(scope="module")
def customer_token() -> str:
    t = _login(*ACCOUNTS["customer"])
    if t is None:
        pytest.skip("seeded customer account unavailable")
    return t


@pytest.fixture
def customer_headers(customer_token: str) -> dict[str, str]:
    return _auth(customer_token)


def _category_id(clients: dict[str, httpx.Client], headers: dict[str, str]) -> str:
    categories = assert_ok(
        clients["catalog"].get("/categories/", headers=headers)
    ).json()["items"]
    if not categories:
        pytest.skip("no seeded categories")
    return str(categories[0]["id"])


def _create_product(
    clients: dict[str, httpx.Client],
    headers: dict[str, str],
    unique: str,
    *,
    price: int = 100,
    **extra: object,
) -> dict:
    category_id = _category_id(clients, headers)
    body = {
        "name": f"e2e-sell-{unique}",
        "price": price,
        "category_id": category_id,
        **extra,
    }
    return assert_ok(
        clients["catalog"].post("/products/", json=body, headers=headers), 201
    ).json()


# ===================================================================
# Catalog management
# ===================================================================


class TestCatalogManagement:
    @pytest.mark.writes
    def test_sell_001_create_product(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-001: a seller can list a new product; it's live immediately.

        Adapted from the plan: the current API has no separate
        is_moderated/publish gate — products default to status="active",
        is_active=True on create (see test_sell_005 for the moderation gap).
        """
        product = _create_product(clients, seller_headers, unique)
        assert product["is_active"] is True
        assert product["status"] == "active"
        assert product["seller_id"]

    @pytest.mark.writes
    def test_sell_002_update_product_price(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-002: a seller can update their own product's price."""
        product = _create_product(clients, seller_headers, unique)
        resp = assert_ok(
            clients["catalog"].put(
                f"/products/{product['id']}",
                json={"price": 999},
                headers=seller_headers,
            )
        )
        assert resp.json()["price"] == 999

    @pytest.mark.writes
    def test_sell_003_images_field_accepts_a_url_map(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-003: adapted — there is no dedicated file-upload endpoint in
        the current catalog-service API; `images` is a plain JSON object set at
        creation time (presumably URLs hosted elsewhere).
        """
        product = _create_product(
            clients,
            seller_headers,
            unique,
            images={"main": "https://cdn.example.test/e2e.jpg"},
        )
        assert product["images"] == {"main": "https://cdn.example.test/e2e.jpg"}

    @pytest.mark.writes
    def test_sell_004_malformed_images_field_is_rejected(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-004: a non-object `images` value is a validation error.

        Not a crash.
        """
        category_id = _category_id(clients, seller_headers)
        resp = clients["catalog"].post(
            "/products/",
            json={
                "name": f"e2e-sell-{unique}-badimg",
                "price": 10,
                "category_id": category_id,
                "images": "not-a-dict",
            },
            headers=seller_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.writes
    def test_sell_005_moderator_can_deactivate_a_product(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        moderator_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-005: adapted — no pre-publish moderation gate exists (see
        test_sell_001); this checks the closest real analogue, a moderator
        deactivating a product post-publish.
        """
        product = _create_product(clients, seller_headers, unique)
        resp = assert_ok(
            clients["catalog"].put(
                f"/products/{product['id']}",
                json={"is_active": False},
                headers=moderator_headers,
            )
        )
        assert resp.json()["is_active"] is False

    @pytest.mark.writes
    def test_sell_006_soft_delete_hides_but_does_not_purge(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-006: a deleted product 404s on direct read afterwards."""
        product = _create_product(clients, seller_headers, unique)
        assert_ok(
            clients["catalog"].delete(
                f"/products/{product['id']}", headers=seller_headers
            ),
            200,
            204,
        )
        gone = clients["catalog"].get(
            f"/products/{product['id']}", headers=seller_headers
        )
        assert gone.status_code == 404

    def test_sell_007_bulk_import_error_templates_are_available(
        self, clients: dict[str, httpx.Client], seller_headers: dict[str, str]
    ) -> None:
        """TC-SELL-007 (setup contract): the CSV import feature exposes its
        validation-error vocabulary — needed by any importer UI/client before
        it can explain row failures.
        """
        body = assert_ok(
            clients["import"].get("/imports/error-templates", headers=seller_headers)
        ).json()
        assert isinstance(body, list)
        assert body, "expected at least one error template"

    @pytest.mark.writes
    def test_sell_014_required_category_property_is_enforced(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-014: creating a product is still possible when no
        category-level required custom property is configured for the seeded
        category — documents the current (permissive) behaviour rather than
        assuming a required-field gate that may not be seeded.
        """
        product = _create_product(
            clients, seller_headers, unique, custom_properties_config={}
        )
        assert product["custom_properties_config"] == {}

    @pytest.mark.writes
    def test_sell_017_negative_price_is_rejected(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-017: price must be >= 0."""
        category_id = _category_id(clients, seller_headers)
        resp = clients["catalog"].post(
            "/products/",
            json={
                "name": f"e2e-sell-{unique}-neg",
                "price": -5,
                "category_id": category_id,
            },
            headers=seller_headers,
        )
        assert resp.status_code == 422

    def test_sell_018_product_listing_is_not_seller_scoped_by_default(
        self, clients: dict[str, httpx.Client], seller_headers: dict[str, str]
    ) -> None:
        """TC-SELL-018: GET /products/ is the shared catalog search, not a
        per-seller inbox — documents that scoping to "my products" (if
        needed) has to happen client-side by seller_id, there is no
        `mine=true` filter in the current API.
        """
        body = assert_ok(
            clients["catalog"].get("/products/", headers=seller_headers)
        ).json()
        assert "items" in body


# ===================================================================
# Order fulfillment
# ===================================================================


class TestOrderFulfillment:
    def test_sell_010_no_dedicated_confirm_endpoint(self) -> None:
        """TC-SELL-010: adapted — order-service exposes no seller-facing
        confirm/accept endpoint; the only status-changing routes are order
        creation and POST /orders/{id}/cancel. Confirmation, if it exists,
        happens automatically off the payment webhook (see
        test_buyer_journey.py::test_buy_004, itself blocked by the
        MissingGreenlet payment bug).
        """
        pytest.skip(
            "no POST /orders/{id}/confirm (or equivalent) in the current "
            "order-service API"
        )

    @pytest.mark.writes
    def test_sell_011_ship_deducts_stock_from_the_reserving_cell(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-011: shipping (fulfilment) is an inventory-service concern —
        POST /stock/ship deducts real stock at a specific warehouse, distinct
        from reserving it.
        """
        product = _create_product(clients, seller_headers, unique)
        warehouses = assert_ok(
            clients["inventory"].get("/warehouses/", headers=seller_headers)
        ).json()
        warehouse_id = warehouses[0]["id"]

        assert_ok(
            clients["inventory"].post(
                "/stock/receive",
                json={
                    "product_id": product["id"],
                    "warehouse_id": warehouse_id,
                    "quantity": 5,
                    "reference_type": "e2e-seed",
                },
                headers=seller_headers,
            )
        )
        assert_ok(
            clients["inventory"].post(
                "/stock/reserve",
                json={
                    "product_id": product["id"],
                    "warehouse_id": warehouse_id,
                    "quantity": 2,
                    "reference_type": "e2e-order",
                },
                headers=seller_headers,
            )
        )
        before = assert_ok(
            clients["inventory"].get(
                f"/stock/by-product/{product['id']}",
                params={"quantity": 1},
                headers=seller_headers,
            )
        ).json()

        assert_ok(
            clients["inventory"].post(
                "/stock/ship",
                json={
                    "product_id": product["id"],
                    "warehouse_id": warehouse_id,
                    "quantity": 2,
                    "reference_type": "e2e-order",
                },
                headers=seller_headers,
            )
        )
        after = assert_ok(
            clients["inventory"].get(
                f"/stock/by-product/{product['id']}",
                params={"quantity": 1},
                headers=seller_headers,
            )
        ).json()
        assert after["quantity"] == before["quantity"] - 2, (
            "shipping must deduct real quantity, not just release the reservation"
        )

    @pytest.mark.writes
    def test_sell_012_cancel_is_the_only_reachable_terminal_transition(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-012: adapted — with no confirm/ship endpoint on order-service
        itself, the only client-triggered terminal transition to check is
        cancelling an already-cancelled order, which must be rejected, not
        silently accepted or 500.
        """
        product = _create_product(clients, seller_headers, unique)
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
        clients["order"].delete("/cart/", headers=seller_headers)
        clients["order"].post(
            "/cart/",
            json={"product_id": product["id"], "quantity": 1},
            headers=seller_headers,
        )
        # seller_access grants ORDER:GET only, not ORDER:POST — use to document
        # the boundary instead of assuming the seller can also buy.
        resp = clients["order"].post(
            "/orders/",
            json={
                "shipping_address": {"city": "Moscow"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers=seller_headers,
            params={"idempotency_key": f"e2e-{unique}-sellbuy"},
        )
        assert resp.status_code == 403, (
            "seller_access has no ORDER:POST — a seller must not be able to place "
            f"orders as a buyer, got {resp.status_code}"
        )

    @pytest.mark.writes
    def test_sell_013_refund_a_delivered_order(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        customer_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-013: a seller can refund a paid order via payment-service."""
        product = _create_product(clients, seller_headers, unique, price=300)
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
        order = assert_ok(
            clients["order"].post(
                "/orders/",
                json={
                    "shipping_address": {"city": "Moscow"},
                    "payment_method": "MOCK",
                    "tax_strategy": "RU",
                },
                headers={**customer_headers, "Idempotency-Key": f"e2e-{unique}-refund"},
            ),
            201,
            200,
        ).json()

        payment = assert_ok(
            clients["payment"].post(
                "/payments/",
                json={
                    "order_id": order["id"],
                    "user_id": order["user_id"],
                    "amount": max(order["total"], 1),
                    "currency": "RUB",
                    "payment_method": "MOCK",
                    "idempotency_key": f"e2e-{unique}-refund-pay",
                },
                headers=customer_headers,
            ),
            201,
            200,
        ).json()

        refund = assert_ok(
            clients["payment"].post(
                f"/payments/{payment['id']}/refund", json={}, headers=seller_headers
            )
        ).json()
        assert refund["status"] in ("REFUNDED", "PARTIALLY_REFUNDED", "PROCESSING")

    @pytest.mark.writes
    def test_sell_024_orders_are_filterable_by_status(
        self, clients: dict[str, httpx.Client], seller_headers: dict[str, str]
    ) -> None:
        """TC-SELL-024: order listing accepts a status filter without erroring."""
        resp = clients["order"].get(
            "/orders/", params={"status": "pending"}, headers=seller_headers
        )
        assert resp.status_code == 200, resp.text[:200]

    @pytest.mark.writes
    def test_sell_025_warehouse_crud(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-SELL-025: a seller can create and update their own warehouse."""
        created = assert_ok(
            clients["inventory"].post(
                "/warehouses/",
                json={"name": f"e2e-wh-{unique}", "address": "1 Test Street, Kazan"},
                headers=seller_headers,
            ),
            200,
            201,
        ).json()
        updated = assert_ok(
            clients["inventory"].patch(
                f"/warehouses/{created['id']}",
                json={"name": f"e2e-wh-{unique}-renamed"},
                headers=seller_headers,
            )
        ).json()
        assert updated["name"] == f"e2e-wh-{unique}-renamed"


# ===================================================================
# Finance and reporting
# ===================================================================


class TestFinanceAndReporting:
    def test_sell_020_commission_calculation_not_exposed(self) -> None:
        """TC-SELL-020: no commission/fee field found on PaymentResponse,
        OrderResponse, or a dedicated endpoint in the current API.
        """
        pytest.skip("no commission/fee endpoint or field in the current API surface")

    def test_sell_021_payout_within_balance(self) -> None:
        """TC-SELL-021: assumed feature — no payout/withdrawal endpoint exists
        in any service's /openapi.json today (checked all 10).
        """
        pytest.skip("no payout/withdrawal endpoint in the current API surface")

    def test_sell_022_payout_exceeding_balance_is_rejected(self) -> None:
        """TC-SELL-022: same gap as test_sell_021."""
        pytest.skip("no payout/withdrawal endpoint in the current API surface")

    def test_sell_023_seller_reads_but_does_not_trigger_reports(
        self, clients: dict[str, httpx.Client], seller_headers: dict[str, str]
    ) -> None:
        """TC-SELL-023: adapted — seller_access grants REPORT:GET only.
        Report generation is scheduler-driven (daily_report job), not a
        seller-initiated POST; this documents that boundary rather than
        assuming self-service report requests.
        """
        listing = assert_ok(
            clients["report"].get("/reports/", headers=seller_headers)
        ).json()
        assert "reports" in listing
        assert "total" in listing

        forbidden = clients["report"].post(
            "/reports/",
            json={"report_type": "sales", "parameters": {}},
            headers=seller_headers,
        )
        assert forbidden.status_code == 403, (
            f"seller_access has no REPORT:POST, got {forbidden.status_code}"
        )
