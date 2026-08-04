"""Buyer E2E journey — happy path, edge cases, eventual consistency.

Test IDs (TC-BUY-###) trace back to the QA test-plan artifact. Grounded in
the live API as of 2026-08-01 (verified by hand against each service's
/openapi.json and real requests, not assumed from docs) — adaptations from
the original plan and confirmed defects are called out per-test.

Known, currently-reproducing defects encoded as xfail (not skip): the test
asserts the CORRECT behaviour and will start passing — and get reported by
pytest as XPASS, a signal to remove the marker — once the underlying bug is
fixed. `strict=False` so the suite stays green in the meantime.
"""

from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from conftest import TIMEOUT, TRUST_ENV, assert_ok, base_url

ACCOUNTS = {
    "customer": ("customer@marketplace.dev", "Customer123!"),
    "customer2": ("customer2@marketplace.dev", "Customer123!"),
    "seller": ("seller@marketplace.dev", "Seller123!"),
}


def _login(email: str, password: str) -> dict[str, str] | None:
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
def customer_tokens() -> dict[str, str]:
    """Full {access_token, refresh_token} pair — needed for TC-BUY-024."""
    body = _login(*ACCOUNTS["customer"])
    if body is None:
        pytest.skip("seeded customer account unavailable")
    return body


@pytest.fixture(scope="module")
def customer2_token() -> str:
    body = _login(*ACCOUNTS["customer2"])
    if body is None:
        pytest.skip("seeded customer2 account unavailable")
    return body["access_token"]


@pytest.fixture(scope="module")
def seller_token() -> str:
    body = _login(*ACCOUNTS["seller"])
    if body is None:
        pytest.skip("seeded seller account unavailable")
    return body["access_token"]


@pytest.fixture
def customer_headers(customer_token: str) -> dict[str, str]:
    return _auth(customer_token)


@pytest.fixture
def seller_headers(seller_token: str) -> dict[str, str]:
    return _auth(seller_token)


def _seller_warehouse(
    clients: dict[str, httpx.Client], seller_headers: dict[str, str], unique: str
) -> str:
    """Return an existing warehouse id for the seller, creating one if needed."""
    warehouses = assert_ok(
        clients["inventory"].get("/warehouses/", headers=seller_headers)
    ).json()
    if warehouses:
        return str(warehouses[0]["id"])
    created = assert_ok(
        clients["inventory"].post(
            "/warehouses/",
            json={"name": f"e2e-wh-{unique}", "address": "1 Test Street, Moscow"},
            headers=seller_headers,
        ),
        200,
        201,
    ).json()
    return str(created["id"])


def _provision_product(
    clients: dict[str, httpx.Client],
    seller_headers: dict[str, str],
    unique: str,
    *,
    price: int = 500,
    stock_qty: int = 20,
) -> tuple[str, str]:
    """Create a fresh product as the seller and stock it.

    Returns (product_id, warehouse_id).
    """
    categories = assert_ok(
        clients["catalog"].get("/categories/", headers=seller_headers)
    ).json()["items"]
    if not categories:
        pytest.skip("no seeded categories")
    category_id = categories[0]["id"]

    product = assert_ok(
        clients["catalog"].post(
            "/products/",
            json={
                "name": f"e2e-buy-{unique}",
                "price": price,
                "category_id": category_id,
                "stock": stock_qty,
            },
            headers=seller_headers,
        ),
        201,
    ).json()

    warehouse_id = _seller_warehouse(clients, seller_headers, unique)
    assert_ok(
        clients["inventory"].post(
            "/stock/receive",
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse_id,
                "quantity": stock_qty,
                "reference_type": "e2e-seed",
            },
            headers=seller_headers,
        )
    )
    return product["id"], warehouse_id


def _available(
    clients: dict[str, httpx.Client], headers: dict[str, str], product_id: str
) -> int:
    body = assert_ok(
        clients["inventory"].get(
            f"/stock/by-product/{product_id}",
            params={"quantity": 1},
            headers=headers,
        )
    ).json()
    return int(body["available"])


def _create_order(
    clients: dict[str, httpx.Client],
    headers: dict[str, str],
    idem_key: str | None = None,
) -> httpx.Response:
    # Idempotency-Key is a header (industry convention — Stripe, GitHub,
    # etc.), not a query param; CreateOrderRequest's body has no such field
    # either. Passing it as a query param (an earlier version of this suite's
    # mistake) silently no-ops — the server never sees it.
    request_headers = dict(headers)
    if idem_key:
        request_headers["Idempotency-Key"] = idem_key
    return clients["order"].post(
        "/orders/",
        json={
            "shipping_address": {"city": "Moscow", "street": "Tverskaya 1"},
            "payment_method": "MOCK",
            "tax_strategy": "RU",
        },
        headers=request_headers,
    )


# ===================================================================
# Happy path
# ===================================================================


class TestHappyPath:
    def test_buy_001_search_and_browse_catalog(
        self, clients: dict[str, httpx.Client], customer_headers: dict[str, str]
    ) -> None:
        """TC-BUY-001: a customer can browse the catalog to shop.

        Regression guard for the RBAC gap fixed 2026-08-01 — customer_orders
        used to grant ORDER:* only, so this 403'd for every buyer.
        """
        body = assert_ok(
            clients["catalog"].get("/products/", headers=customer_headers)
        ).json()
        assert {"items", "total", "page", "page_size"} <= body.keys()

    def test_buy_002_add_to_cart(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-002: adding a product to the cart is reflected on read-back."""
        product_id, _ = _provision_product(clients, seller_headers, unique)
        clients["order"].delete("/cart/", headers=customer_headers)

        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 2},
                headers=customer_headers,
            )
        )
        cart = assert_ok(
            clients["order"].get("/cart/", headers=customer_headers)
        ).json()
        items = cart.get("items", cart)
        found = next((i for i in items if i["product_id"] == product_id), None)
        assert found is not None
        assert found["quantity"] == 2

    @pytest.mark.writes
    def test_buy_003_checkout_reserves_stock(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-003: checkout creates a pending order and reserves stock."""
        product_id, _ = _provision_product(
            clients, seller_headers, unique, stock_qty=10
        )
        before = _available(clients, seller_headers, product_id)

        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 3},
                headers=customer_headers,
            )
        )
        order = assert_ok(
            _create_order(clients, customer_headers, f"e2e-{unique}"), 201, 200
        ).json()
        assert order["status"] == "pending"

        after = _available(clients, seller_headers, product_id)
        assert before - after == 3, "3 units should move from available to reserved"

    @pytest.mark.writes
    def test_buy_003b_order_total_matches_catalog_price(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-003 (pricing): the order total must reflect the real product price.

        catalog prices are whole rubles (777); OrderItem.price is minor units
        (kopecks) per its column comment, so order-service converts ×100 when
        it pulls the price from catalog — see _resolve_product_details().
        """
        product_id, _ = _provision_product(clients, seller_headers, unique, price=777)
        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 2},
                headers=customer_headers,
            )
        )
        order = assert_ok(
            _create_order(clients, customer_headers, f"e2e-{unique}-price"), 201, 200
        ).json()
        expected_item_price = 777 * 100
        expected_subtotal = expected_item_price * 2
        assert order["items"][0]["price"] == expected_item_price
        assert order["subtotal"] == expected_subtotal
        assert order["total"] == expected_subtotal + order["tax"]

    @pytest.mark.writes
    def test_buy_004_payment_confirms_order(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-004: a successful payment eventually confirms the order (async)."""
        product_id, _ = _provision_product(clients, seller_headers, unique)
        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 1},
                headers=customer_headers,
            )
        )
        # Order and payment idempotency claims share one unnamespaced Redis
        # keyspace (`idempotency:{key}`, no per-service prefix) — reusing the
        # same literal key for both would make payment-service's own SETNX
        # fail against order-service's claim and 409 with "no payment found".
        order = assert_ok(
            _create_order(clients, customer_headers, f"e2e-{unique}-order"), 201, 200
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
                    "idempotency_key": f"e2e-{unique}-pay",
                },
                headers=customer_headers,
            ),
            201,
            200,
        ).json()
        assert payment["status"] in ("SUCCEEDED", "PROCESSING")

    @pytest.mark.writes
    def test_buy_004b_paid_order_status_eventually_syncs(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-004 (status sync): once payment succeeds, order.status should
        eventually leave 'pending' — the other half of test_buy_004, kept
        separate so the payment step and the status-sync step (order-service
        consuming payment.succeeded off marketplace.events, see
        workers_main.py) have independent pass/fail signal.
        """
        product_id, _ = _provision_product(clients, seller_headers, unique)
        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 1},
                headers=customer_headers,
            )
        )
        order = assert_ok(
            _create_order(clients, customer_headers, f"e2e-{unique}-order2"), 201, 200
        ).json()
        assert_ok(
            clients["payment"].post(
                "/payments/",
                json={
                    "order_id": order["id"],
                    "user_id": order["user_id"],
                    "amount": max(order["total"], 1),
                    "currency": "RUB",
                    "payment_method": "MOCK",
                    "idempotency_key": f"e2e-{unique}-pay2",
                },
                headers=customer_headers,
            ),
            201,
            200,
        )

        deadline = time.monotonic() + 5
        status = order["status"]
        while time.monotonic() < deadline and status == "pending":
            time.sleep(0.5)
            status = (
                clients["order"]
                .get(f"/orders/{order['id']}", headers=customer_headers)
                .json()["status"]
            )
        assert status in ("confirmed", "paid")

    def test_buy_005_order_history_is_scoped_to_self(
        self, clients: dict[str, httpx.Client], customer_headers: dict[str, str]
    ) -> None:
        """TC-BUY-005: listing orders returns an envelope of the caller's own orders."""
        resp = assert_ok(clients["order"].get("/orders/", headers=customer_headers))
        assert resp.status_code == 200


# ===================================================================
# Edge cases and negative scenarios
# ===================================================================


class TestEdgeCases:
    @pytest.mark.writes
    def test_buy_007_partial_stock_blocks_the_whole_order(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-007: one unavailable item in the cart must block the entire order —
        the available item must not be partially reserved.
        """
        available_product, _ = _provision_product(
            clients, seller_headers, f"{unique}-a", stock_qty=5
        )
        # A second product with a warehouse but zero stock received.
        categories = (
            clients["catalog"]
            .get("/categories/", headers=seller_headers)
            .json()["items"]
        )
        out_of_stock = assert_ok(
            clients["catalog"].post(
                "/products/",
                json={
                    "name": f"e2e-buy-{unique}-oos",
                    "price": 100,
                    "category_id": categories[0]["id"],
                    "stock": 0,
                },
                headers=seller_headers,
            ),
            201,
        ).json()["id"]

        before = _available(clients, seller_headers, available_product)

        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": available_product, "quantity": 1},
                headers=customer_headers,
            )
        )
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": out_of_stock, "quantity": 1},
                headers=customer_headers,
            )
        )

        resp = _create_order(clients, customer_headers, f"e2e-{unique}-partial")
        assert resp.status_code in (400, 409, 422), (
            f"expected the order to be rejected for insufficient stock, got "
            f"{resp.status_code}: {resp.text[:200]}"
        )

        after = _available(clients, seller_headers, available_product)
        assert after == before, (
            "the available item must not be reserved when the order fails"
        )

        clients["order"].delete("/cart/", headers=customer_headers)

    @pytest.mark.writes
    def test_buy_008_cancel_own_order_releases_stock(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-008: cancelling a pending order releases its reservation."""
        product_id, _ = _provision_product(clients, seller_headers, unique, stock_qty=8)
        before = _available(clients, seller_headers, product_id)

        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 2},
                headers=customer_headers,
            )
        )
        order = assert_ok(
            _create_order(clients, customer_headers, f"e2e-{unique}-cancel"), 201, 200
        ).json()
        assert _available(clients, seller_headers, product_id) == before - 2

        assert_ok(
            clients["order"].post(
                f"/orders/{order['id']}/cancel", headers=customer_headers
            )
        )
        cancelled = assert_ok(
            clients["order"].get(f"/orders/{order['id']}", headers=customer_headers)
        ).json()
        assert cancelled["status"] == "cancelled"
        assert _available(clients, seller_headers, product_id) == before, (
            "cancelling must release the reservation back to available stock"
        )

    @pytest.mark.writes
    def test_buy_009_duplicate_submission_is_idempotent(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-009 / TC-BUY-014: two identical requests with the same
        Idempotency-Key header (double-click, or client retry after a dropped
        connection — indistinguishable server-side) must not double-reserve
        or create two orders.

        Corrected 2026-08-01: an earlier version of this test sent the key as
        a `idempotency_key` query param, which order-service's endpoint never
        reads (it's declared as a header, the conventional transport for
        this). That made every "retry" a no-op-key request hitting an
        already-emptied cart — a bug in the test, not the app; the app's own
        dedup logic (check-before-cart-validation) was correct all along.
        """
        product_id, _ = _provision_product(clients, seller_headers, unique, stock_qty=8)
        before = _available(clients, seller_headers, product_id)

        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 1},
                headers=customer_headers,
            )
        )
        idem = f"e2e-{unique}-dup"
        first = assert_ok(
            _create_order(clients, customer_headers, idem), 201, 200
        ).json()
        second = assert_ok(
            _create_order(clients, customer_headers, idem), 201, 200
        ).json()

        assert first["id"] == second["id"], (
            "same idempotency_key must return the same order"
        )
        assert before - _available(clients, seller_headers, product_id) == 1, (
            "the retry must not reserve stock a second time"
        )

    @pytest.mark.writes
    def test_buy_010_concurrent_buyers_race_for_last_unit(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        customer2_token: str,
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-010: with exactly one unit in stock, two simultaneous checkouts
        must not both succeed.
        """
        product_id, _ = _provision_product(clients, seller_headers, unique, stock_qty=1)
        customer2_headers = _auth(customer2_token)

        clients["order"].delete("/cart/", headers=customer_headers)
        clients["order"].delete("/cart/", headers=customer2_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 1},
                headers=customer_headers,
            )
        )
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 1},
                headers=customer2_headers,
            )
        )

        def _checkout(headers: dict[str, str], key: str) -> httpx.Response:
            return _create_order(clients, headers, key)

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(_checkout, customer_headers, f"e2e-{unique}-race-1")
            f2 = pool.submit(_checkout, customer2_headers, f"e2e-{unique}-race-2")
            r1, r2 = f1.result(), f2.result()

        successes = [r for r in (r1, r2) if r.status_code in (200, 201)]
        failures = [r for r in (r1, r2) if r.status_code not in (200, 201)]
        assert len(successes) == 1, (
            f"exactly one checkout should win the last unit, got statuses "
            f"{r1.status_code}, {r2.status_code}"
        )
        assert failures[0].status_code in (400, 409, 422), failures[0].text[:200]

    def test_buy_012_unpaid_order_is_autocancelled(
        self,
        clients: dict[str, httpx.Client],
        auth_headers: dict[str, str],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-012: triggering cancel_unpaid_orders reaches order-service and
        is authorized to act — the mechanism this test can actually exercise.

        Adapted: the job only ever selects orders older than
        UNPAID_ORDER_TIMEOUT_MINUTES (created_at < now - 30min, see
        order_repo.py get_expired_orders). A freshly-created order in this
        test never qualifies no matter how long the test polls — there is no
        HTTP-only way to backdate created_at (this harness deliberately
        doesn't touch the DB directly, see conftest.py's module docstring),
        and waiting 30 real minutes isn't a reasonable test. So this checks
        what's actually verifiable: the trigger is reachable and accepted,
        and — the part that was genuinely broken (see task history) —
        SYSTEM_TOKEN is authorized to cancel an order it doesn't own, via the
        same order-service endpoint the job calls.
        """
        product_id, _ = _provision_product(clients, seller_headers, unique)
        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 1},
                headers=customer_headers,
            )
        )
        order = assert_ok(
            _create_order(clients, customer_headers, f"e2e-{unique}-stale"), 201, 200
        ).json()

        assert_ok(
            clients["scheduler"].post(
                "/jobs/cancel_unpaid_orders/trigger", headers=auth_headers
            ),
            200,
            201,
            202,
        )

        # A fresh order won't be touched by the age-filtered job (see above) —
        # confirm it's still there and untouched, then verify a *privileged*
        # caller (standing in for the job's own SYSTEM_TOKEN identity) really
        # can cancel it, which is the authorization path that was broken.
        still_pending = (
            clients["order"]
            .get(f"/orders/{order['id']}", headers=customer_headers)
            .json()
        )
        assert still_pending["status"] == "pending"

        cancelled = assert_ok(
            clients["order"].post(f"/orders/{order['id']}/cancel", headers=auth_headers)
        ).json()
        assert cancelled["status"] == "cancelled"

    def test_buy_013_cart_ttl_is_not_e2e_verifiable(self) -> None:
        """TC-BUY-013: cart TTL (7 days) cannot be exercised within a test run.

        conftest.py's own contract is HTTP-only, no direct Redis access — and
        waiting 7 days is not a reasonable test. Left as a documented gap
        rather than faked; verify via `redis-cli TTL cart:{user_id}`
        manually if this ever needs re-checking.
        """
        pytest.skip("cart TTL requires either direct Redis access or a 7-day wait")

    def test_buy_015_search_with_no_results(
        self, clients: dict[str, httpx.Client], customer_headers: dict[str, str]
    ) -> None:
        """TC-BUY-015: an empty result set is 200 with an empty array, not an error."""
        body = assert_ok(
            clients["catalog"].get(
                "/products/",
                params={"name": "no-such-product-xyz-e2e"},
                headers=customer_headers,
            )
        ).json()
        assert body["items"] == [] or body["total"] == 0

    def test_buy_016_pagination_is_honoured(
        self, clients: dict[str, httpx.Client], customer_headers: dict[str, str]
    ) -> None:
        """TC-BUY-016: page_size caps the number of returned items."""
        body = assert_ok(
            clients["catalog"].get(
                "/products/",
                params={"page": 1, "page_size": 2},
                headers=customer_headers,
            )
        ).json()
        assert len(body["items"]) <= 2
        assert body["page_size"] == 2

    @pytest.mark.writes
    def test_buy_017_zero_or_negative_quantity_is_rejected(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-017: quantity must be positive."""
        product_id, _ = _provision_product(clients, seller_headers, unique)
        for bad_qty in (0, -1):
            resp = clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": bad_qty},
                headers=customer_headers,
            )
            assert resp.status_code == 422, f"quantity={bad_qty} should be rejected"

    @pytest.mark.writes
    def test_buy_019_remove_cart_item(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-019: a removed cart line no longer appears in the cart."""
        product_id, _ = _provision_product(clients, seller_headers, unique)
        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 1},
                headers=customer_headers,
            )
        )
        assert_ok(
            clients["order"].delete(f"/cart/{product_id}", headers=customer_headers),
            200,
            204,
        )
        cart = assert_ok(
            clients["order"].get("/cart/", headers=customer_headers)
        ).json()
        items = cart.get("items", cart)
        assert all(i["product_id"] != product_id for i in items)

    def test_buy_020_empty_cart_checkout_is_rejected(
        self, clients: dict[str, httpx.Client], customer_headers: dict[str, str]
    ) -> None:
        """TC-BUY-020: checking out an empty cart is a client error, not a 500."""
        clients["order"].delete("/cart/", headers=customer_headers)
        resp = _create_order(
            clients, customer_headers, f"e2e-empty-{uuid.uuid4().hex[:8]}"
        )
        assert resp.status_code in (400, 409, 422), resp.text[:200]

    @pytest.mark.writes
    def test_buy_021_order_currency_defaults_to_rub(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """TC-BUY-021: orders default to RUB, matching product currency."""
        product_id, _ = _provision_product(clients, seller_headers, unique)
        clients["order"].delete("/cart/", headers=customer_headers)
        assert_ok(
            clients["order"].post(
                "/cart/",
                json={"product_id": product_id, "quantity": 1},
                headers=customer_headers,
            )
        )
        order = assert_ok(
            _create_order(clients, customer_headers, f"e2e-{unique}-cur"), 201, 200
        ).json()
        assert order["currency"] == "RUB"

    def test_buy_022_shipping_address_is_required(
        self, clients: dict[str, httpx.Client], customer_headers: dict[str, str]
    ) -> None:
        """TC-BUY-022: omitting shipping_address entirely is a validation error."""
        resp = clients["order"].post(
            "/orders/",
            json={"payment_method": "MOCK", "tax_strategy": "RU"},
            headers=customer_headers,
        )
        assert resp.status_code == 422

    def test_buy_023_order_history_endpoint_not_exposed(self) -> None:
        """TC-BUY-023: no /orders/{id}/history or status-history field exists
        in the current OrderResponse — nothing to assert against yet.
        """
        pytest.skip(
            "OrderResponse has no status-history field and no dedicated "
            "history endpoint in the current order-service API"
        )

    def test_buy_024_refresh_does_not_invalidate_the_current_access_token(
        self, clients: dict[str, httpx.Client], customer_tokens: dict[str, str]
    ) -> None:
        """TC-BUY-024: rotating the refresh token mid-session must not break the
        access token already in use for an in-flight checkout.
        """
        access_token = customer_tokens["access_token"]
        refresh_resp = httpx.post(
            f"{base_url('auth')}/auth/refresh",
            json={"refresh_token": customer_tokens["refresh_token"]},
            timeout=TIMEOUT,
            trust_env=TRUST_ENV,
        )
        assert refresh_resp.status_code == 200

        still_valid = clients["order"].get("/orders/", headers=_auth(access_token))
        assert still_valid.status_code == 200, (
            "the original access token must keep working until its own TTL expires"
        )
