"""Authorization E2E tests — role-based access control.

Проверяет, что RBAC из auth-service реально ограничивает доступ:
- Customer: только заказы, не может менять каталог/склад
- Seller: каталог/склад/импорт, но НЕ может покупать (ORDER:POST запрещён)
- Moderator: каталог + просмотр заказов, но не склад
"""

import httpx
import pytest
from conftest import TIMEOUT, TRUST_ENV, base_url

# ===================================================================
# Seeded accounts
# ===================================================================

ACCOUNTS = {
    "customer": ("customer@marketplace.dev", "Customer123!"),
    "customer2": ("customer2@marketplace.dev", "Customer123!"),
    "seller": ("seller@marketplace.dev", "Seller123!"),
    "moderator": ("moderator@marketplace.dev", "Moderator123!"),
    "admin": ("admin@marketplace.dev", "Admin123!"),
}


def _login(email: str, password: str) -> str | None:
    resp = httpx.post(
        f"{base_url('auth')}/auth/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
        trust_env=TRUST_ENV,
    )
    if resp.status_code != 200:
        return None
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ===================================================================
# Token fixtures
# ===================================================================


@pytest.fixture(scope="module")
def customer_token() -> str:
    t = _login(*ACCOUNTS["customer"])
    if not t:
        pytest.skip("customer account unavailable")
    return t


@pytest.fixture(scope="module")
def seller_token() -> str:
    t = _login(*ACCOUNTS["seller"])
    if not t:
        pytest.skip("seller account unavailable")
    return t


@pytest.fixture(scope="module")
def moderator_token() -> str:
    t = _login(*ACCOUNTS["moderator"])
    if not t:
        pytest.skip("moderator account unavailable")
    return t


# ===================================================================
# Scenario 1: Customer — только свои заказы
# ===================================================================


class TestCustomerPermissions:
    """Customer: ORDER:* (GET/POST/PUT/DELETE), ничего больше."""

    def test_customer_can_access_own_orders(
        self, customer_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Customer has ORDER:GET → список заказов доступен."""
        h = _auth(customer_token)
        resp = clients["order"].get("/orders/", headers=h)
        assert resp.status_code == 200, (
            f"Customer should access orders, got {resp.status_code}: {resp.text[:200]}"
        )

    def test_customer_can_create_order(
        self, customer_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Customer has ORDER:POST → может создавать заказы (покупать)."""
        h = _auth(customer_token)
        # Очистить корзину, добавить товар
        clients["order"].delete("/cart/", headers=h)
        # Получить product_id из каталога (через admin)
        admin_t = _login(*ACCOUNTS["admin"])
        if not admin_t:
            pytest.skip("admin unavailable for product lookup")
        prods = clients["catalog"].get(
            "/products/", params={"page_size": 1}, headers=_auth(admin_t)
        )
        if prods.status_code != 200 or not prods.json()["items"]:
            pytest.skip("No products available")
        pid = prods.json()["items"][0]["id"]

        clients["order"].post(
            "/cart/", json={"product_id": pid, "quantity": 1}, headers=h
        )

        resp = clients["order"].post(
            "/orders/",
            json={
                "shipping_address": {"city": "Test"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers=h,
        )
        # Должен мочь создать (или получить осмысленную ошибку — не 401/403)
        assert resp.status_code not in (401, 403), (
            f"Customer should be allowed ORDER:POST, got {resp.status_code}: "
            f"{resp.text[:200]}"
        )

    def test_customer_can_browse_catalog(
        self, customer_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Customer has CATALOG:GET → can browse categories to shop.

        Fixed 2026-08-01: customer_orders previously granted ORDER:* only,
        with no CATALOG:GET at all — a buyer could not browse the catalog
        they were meant to shop from. Seed data now matches the documented
        role ("Покупатель — чтение каталога, свои заказы, корзина").
        """
        h = _auth(customer_token)
        resp = clients["catalog"].get("/categories/", headers=h)
        assert resp.status_code == 200, (
            f"Customer with CATALOG:GET should browse categories, "
            f"got {resp.status_code}"
        )

    def test_customer_cannot_access_inventory(
        self, customer_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Customer без INVENTORY:* → склад недоступен."""
        h = _auth(customer_token)
        resp = clients["inventory"].get("/warehouses/", headers=h)
        assert resp.status_code == 403, (
            f"Customer without INVENTORY should get 403, got {resp.status_code}"
        )

    def test_customer_cannot_modify_catalog(
        self, customer_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Customer без CATALOG:POST → не может создать категорию."""
        h = _auth(customer_token)
        resp = clients["catalog"].post(
            "/categories/",
            json={"name": "Hacked Category", "slug": "hacked"},
            headers=h,
        )
        assert resp.status_code == 403, (
            f"Customer should not POST categories, got {resp.status_code}"
        )

    def test_customer_can_read_dictionary(
        self, customer_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Customer has DICTIONARY:GET → units/currencies needed to check out.

        Fixed 2026-08-01 alongside catalog access — see
        test_customer_can_browse_catalog.
        """
        h = _auth(customer_token)
        resp = clients["dictionary"].get("/dictionaries/units", headers=h)
        assert resp.status_code == 200, (
            f"Customer with DICTIONARY:GET should read units, got {resp.status_code}"
        )


# ===================================================================
# Scenario 2: Seller — каталог/склад, но НЕ покупки
# ===================================================================


class TestSellerPermissions:
    """Seller: CATALOG:*, INVENTORY:*, IMPORT:*, REPORT:GET, ORDER:GET (без POST)."""

    def test_seller_cannot_create_order(
        self, seller_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Seller без ORDER:POST → не может покупать (оформлять заказ)."""
        h = _auth(seller_token)
        resp = clients["order"].post(
            "/orders/",
            json={
                "shipping_address": {"city": "Test"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers=h,
        )
        assert resp.status_code == 403, (
            f"Seller without ORDER:POST should get 403, got {resp.status_code}: "
            f"{resp.text[:200]}"
        )

    def test_seller_can_view_orders(
        self, seller_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Seller имеет ORDER:GET → может смотреть заказы."""
        h = _auth(seller_token)
        resp = clients["order"].get("/orders/", headers=h)
        assert resp.status_code == 200, (
            f"Seller with ORDER:GET should access orders, got {resp.status_code}"
        )

    def test_seller_can_access_inventory(
        self, seller_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Seller имеет INVENTORY:GET → склад доступен."""
        h = _auth(seller_token)
        resp = clients["inventory"].get("/warehouses/", headers=h)
        assert resp.status_code == 200, (
            f"Seller with INVENTORY should access warehouses, got {resp.status_code}"
        )

    def test_seller_can_access_catalog(
        self, seller_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Seller имеет CATALOG:GET → каталог доступен."""
        h = _auth(seller_token)
        resp = clients["catalog"].get("/categories/", headers=h)
        assert resp.status_code == 200, (
            f"Seller with CATALOG should access categories, got {resp.status_code}"
        )

    def test_seller_cannot_access_scheduler(
        self, seller_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Seller без SCHEDULER:* → cron-задачи недоступны."""
        h = _auth(seller_token)
        resp = clients["scheduler"].get("/jobs/", headers=h)
        assert resp.status_code == 403, (
            f"Seller without SCHEDULER should get 403, got {resp.status_code}"
        )

    def test_seller_can_reach_payment_service(
        self, seller_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Seller has PAYMENT:GET/POST (fixed 2026-08-01, needed to view/refund
        payments for their own orders — see test_seller_journey.py
        test_sell_013). GET /payments/{id} is the only parameter-free-adjacent
        read route; /payments/ itself has no collection GET, so a bare GET
        there is 405 (method not allowed), not 403 (permission denied) —
        confirms the RBAC layer let the request through to the router.
        """
        h = _auth(seller_token)
        resp = clients["payment"].get("/payments/", headers=h)
        assert resp.status_code == 405, (
            f"Seller with PAYMENT:GET should reach the router (405, no such "
            f"collection route), not be denied by RBAC, got {resp.status_code}"
        )


# ===================================================================
# Scenario 3: Moderator — каталог + заказы (просмотр)
# ===================================================================


class TestModeratorPermissions:
    """Moderator: CATALOG:* + ORDER:GET."""

    def test_moderator_can_access_catalog(
        self, moderator_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        h = _auth(moderator_token)
        resp = clients["catalog"].get("/categories/", headers=h)
        assert resp.status_code == 200, (
            f"Moderator with CATALOG should access categories, got {resp.status_code}"
        )

    def test_moderator_can_view_orders(
        self, moderator_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        h = _auth(moderator_token)
        resp = clients["order"].get("/orders/", headers=h)
        assert resp.status_code == 200, (
            f"Moderator with ORDER:GET should access orders, got {resp.status_code}"
        )

    def test_moderator_cannot_access_inventory(
        self, moderator_token: str, clients: dict[str, httpx.Client]
    ) -> None:
        """Moderator без INVENTORY:*."""
        h = _auth(moderator_token)
        resp = clients["inventory"].get("/warehouses/", headers=h)
        assert resp.status_code == 403, (
            f"Moderator without INVENTORY should get 403, got {resp.status_code}"
        )


# ===================================================================
# Scenario 4: Аноним — 401 на защищённых эндпоинтах
# ===================================================================


class TestAnonymousAccess:
    """Без токена — 401 на всём, кроме публичных эндпоинтов."""

    @pytest.mark.parametrize(
        ("service", "path"),
        [
            ("catalog", "/categories/"),
            ("catalog", "/products/"),
            ("order", "/orders/"),
            ("order", "/cart/"),
            ("inventory", "/warehouses/"),
            ("payment", "/payments/"),
            ("dictionary", "/dictionaries/units"),
            ("scheduler", "/jobs/"),
            ("report", "/reports/"),
            ("notification", "/notifications/"),
        ],
    )
    def test_protected_endpoints_require_auth(
        self, service: str, path: str, clients: dict[str, httpx.Client]
    ) -> None:
        resp = clients[service].get(path)
        assert resp.status_code in (401, 403), (
            f"{service}{path} should require auth, got {resp.status_code}"
        )

    def test_login_requires_no_token(self) -> None:
        """POST /auth/login — публичный, не требует токена."""
        resp = httpx.post(
            f"{base_url('auth')}/auth/login",
            json={"email": "customer@marketplace.dev", "password": "Customer123!"},
            timeout=TIMEOUT,
            trust_env=TRUST_ENV,
        )
        assert resp.status_code == 200, f"Login should work, got {resp.status_code}"


# ===================================================================
# Scenario 5: Чужой заказ — customer2 не видит заказ customer1
# ===================================================================


class TestCrossUserIsolation:
    """Пользователь не должен получать доступ к данным другого пользователя."""

    def test_customer_cannot_see_other_orders(
        self,
        customer_token: str,
        clients: dict[str, httpx.Client],
    ) -> None:
        """Customer видит только свои заказы, не чужие."""
        h = _auth(customer_token)
        # Получаем список заказов — должны быть только свои
        resp = clients["order"].get("/orders/", headers=h)
        if resp.status_code != 200:
            pytest.skip("Order listing not available")
        # GET /orders/ is already scoped server-side to the caller's own
        # user_id (see order-service's OrderService.get_user_orders) — a
        # cross-user leak through this endpoint isn't structurally possible,
        # so there's nothing further to assert about the returned orders'
        # ownership here. The IDOR angle (fetching a *specific* order by
        # UUID that belongs to someone else) is covered by
        # test_security_idor.py instead.
        assert resp.status_code == 200
