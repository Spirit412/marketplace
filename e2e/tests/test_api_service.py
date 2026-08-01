"""api-service — BFF/composition endpoints.

Covers the two v1 composed endpoints from PLAN_api-service.md:
GET /storefront/products/{id} (catalog + inventory) and
GET /orders/{id}/full (order + the new payment-service GET
/payments/by-order/{id}). Direct access to every underlying service stays
supported — these tests exercise the composition path specifically, not a
replacement for test_buyer_journey.py's direct-service coverage.
"""

import httpx
import pytest
from conftest import TIMEOUT, TRUST_ENV, assert_ok, base_url

SERVICE = "api"

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
def customer2_headers(customer2_token: str) -> dict[str, str]:
    return _auth(customer2_token)


@pytest.fixture
def seller_headers(seller_token: str) -> dict[str, str]:
    return _auth(seller_token)


def _seller_warehouse(
    clients: dict[str, httpx.Client], seller_headers: dict[str, str], unique: str
) -> str:
    warehouses = assert_ok(
        clients["inventory"].get("/warehouses/", headers=seller_headers)
    ).json()
    if warehouses:
        return str(warehouses[0]["id"])
    created = assert_ok(
        clients["inventory"].post(
            "/warehouses/",
            json={"name": f"e2e-api-wh-{unique}", "address": "1 Test Street, Moscow"},
            headers=seller_headers,
        ),
        200,
        201,
    ).json()
    return str(created["id"])


def _provision_product(
    clients: dict[str, httpx.Client], seller_headers: dict[str, str], unique: str
) -> str:
    categories = assert_ok(
        clients["catalog"].get("/categories/", headers=seller_headers)
    ).json()["items"]
    if not categories:
        pytest.skip("no seeded categories")
    product = assert_ok(
        clients["catalog"].post(
            "/products/",
            json={
                "name": f"e2e-api-{unique}",
                "price": 500,
                "category_id": categories[0]["id"],
                "stock": 20,
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
                "quantity": 20,
                "reference_type": "e2e-seed",
            },
            headers=seller_headers,
        )
    )
    return str(product["id"])


def _create_order(
    clients: dict[str, httpx.Client],
    customer_headers: dict[str, str],
    seller_headers: dict[str, str],
    unique: str,
) -> dict:
    product_id = _provision_product(clients, seller_headers, unique)
    clients["order"].delete("/cart/", headers=customer_headers)
    assert_ok(
        clients["order"].post(
            "/cart/",
            json={"product_id": product_id, "quantity": 1},
            headers=customer_headers,
        )
    )
    return assert_ok(
        clients["order"].post(
            "/orders/",
            json={
                "shipping_address": {"city": "Moscow", "street": "Tverskaya 1"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers={**customer_headers, "Idempotency-Key": f"e2e-api-{unique}-order"},
        ),
        201,
        200,
    ).json()


class TestStorefrontComposition:
    def test_product_card_includes_live_stock(
        self,
        clients: dict[str, httpx.Client],
        seller_headers: dict[str, str],
        customer_headers: dict[str, str],
        unique: str,
    ) -> None:
        """The whole point of this endpoint: one call gets both the catalog
        record and a stock number that's actually current, not catalog's
        own stale `stock` column (see StorefrontProductResponse's docstring).
        """
        product_id = _provision_product(clients, seller_headers, unique)

        body = assert_ok(
            clients["api"].get(
                f"/storefront/products/{product_id}", headers=customer_headers
            )
        ).json()

        assert body["id"] == product_id
        assert body["available"] == 20
        assert body["warehouse_id"] is not None
        assert "stock" not in body  # catalog's stale field must not leak through

    def test_unknown_product_is_404(
        self, clients: dict[str, httpx.Client], customer_headers: dict[str, str]
    ) -> None:
        resp = clients["api"].get(
            "/storefront/products/00000000-0000-0000-0000-000000000000",
            headers=customer_headers,
        )
        assert resp.status_code == 404


class TestOrderFullComposition:
    @pytest.mark.writes
    def test_pending_order_has_no_payment_yet(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        order = _create_order(clients, customer_headers, seller_headers, unique)

        body = assert_ok(
            clients["api"].get(f"/orders/{order['id']}/full", headers=customer_headers)
        ).json()

        assert body["id"] == order["id"]
        assert body["payment"] is None

    @pytest.mark.writes
    def test_paid_order_shows_payment_status(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        order = _create_order(clients, customer_headers, seller_headers, unique)
        assert_ok(
            clients["payment"].post(
                "/payments/",
                json={
                    "order_id": order["id"],
                    "user_id": order["user_id"],
                    "amount": max(order["total"], 1),
                    "currency": "RUB",
                    "payment_method": "MOCK",
                    "idempotency_key": f"e2e-api-{unique}-pay",
                },
                headers=customer_headers,
            ),
            201,
            200,
        )

        # Payment creation is synchronous (unlike order-status sync off
        # marketplace.events), so no polling loop is needed here.
        body = assert_ok(
            clients["api"].get(f"/orders/{order['id']}/full", headers=customer_headers)
        ).json()

        assert body["payment"] is not None
        assert body["payment"]["status"] in ("SUCCEEDED", "PROCESSING", "PENDING")

    @pytest.mark.writes
    def test_customer_cannot_read_anothers_order_through_composition(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        customer2_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """IDOR check specific to the composition path — order-service's own
        ownership check (see PLAN_order-service.md) must survive being
        called through api-service's forwarded token, not just direct
        access (already covered by test_security_idor.py).
        """
        order = _create_order(clients, customer_headers, seller_headers, unique)

        resp = clients["api"].get(
            f"/orders/{order['id']}/full", headers=customer2_headers
        )
        assert resp.status_code == 404

    def test_unknown_order_is_404(
        self, clients: dict[str, httpx.Client], customer_headers: dict[str, str]
    ) -> None:
        resp = clients["api"].get(
            "/orders/00000000-0000-0000-0000-000000000000/full",
            headers=customer_headers,
        )
        assert resp.status_code == 404


class TestPaymentByOrderDirectly:
    """payment-service's new GET /payments/by-order/{id} — same endpoint
    api-service's OrderFacade calls, tested here without api-service in the
    loop so a regression is traceable to the right service.
    """

    @pytest.mark.writes
    def test_no_payment_yet_is_404(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        order = _create_order(clients, customer_headers, seller_headers, unique)
        resp = clients["payment"].get(
            f"/payments/by-order/{order['id']}", headers=customer_headers
        )
        assert resp.status_code == 404

    @pytest.mark.writes
    def test_owner_can_read_it_after_paying(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        order = _create_order(clients, customer_headers, seller_headers, unique)
        assert_ok(
            clients["payment"].post(
                "/payments/",
                json={
                    "order_id": order["id"],
                    "user_id": order["user_id"],
                    "amount": max(order["total"], 1),
                    "currency": "RUB",
                    "payment_method": "MOCK",
                    "idempotency_key": f"e2e-api-{unique}-pay-direct",
                },
                headers=customer_headers,
            ),
            201,
            200,
        )

        body = assert_ok(
            clients["payment"].get(
                f"/payments/by-order/{order['id']}", headers=customer_headers
            )
        ).json()
        assert body["order_id"] == order["id"]

    @pytest.mark.writes
    def test_non_owner_gets_404_not_someone_elses_payment(
        self,
        clients: dict[str, httpx.Client],
        customer_headers: dict[str, str],
        customer2_headers: dict[str, str],
        seller_headers: dict[str, str],
        unique: str,
    ) -> None:
        """The IDOR gap this endpoint was built without repeating — see
        PLAN_api-service.md's note on GET /payments/{payment_uuid} having
        had no ownership check at all before this change.
        """
        order = _create_order(clients, customer_headers, seller_headers, unique)
        assert_ok(
            clients["payment"].post(
                "/payments/",
                json={
                    "order_id": order["id"],
                    "user_id": order["user_id"],
                    "amount": max(order["total"], 1),
                    "currency": "RUB",
                    "payment_method": "MOCK",
                    "idempotency_key": f"e2e-api-{unique}-pay-idor",
                },
                headers=customer_headers,
            ),
            201,
            200,
        )

        resp = clients["payment"].get(
            f"/payments/by-order/{order['id']}", headers=customer2_headers
        )
        assert resp.status_code == 404


class TestHealthAndDocs:
    def test_health_is_public(self, clients: dict[str, httpx.Client]) -> None:
        resp = clients["api"].get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["service"] == "api-service"

    def test_swagger_is_enabled_on_api_service(
        self, clients: dict[str, httpx.Client]
    ) -> None:
        """The one service where interactive docs are deliberately kept —
        see main.py's docs_url comment on every other service.
        """
        resp = clients["api"].get("/docs")
        assert resp.status_code == 200

    @pytest.mark.parametrize("service", ["catalog", "order", "payment", "inventory"])
    def test_swagger_is_disabled_on_domain_services(
        self, clients: dict[str, httpx.Client], service: str
    ) -> None:
        resp = clients[service].get("/docs")
        assert resp.status_code == 404
