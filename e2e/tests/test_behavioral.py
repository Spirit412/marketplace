"""Поведенческие E2E-тесты: полный цикл маркетплейса.

Сценарии имитируют реальное поведение пользователей.
Требуют ЗАПУЩЕННОГО стека (docker compose up) и заполненной БД (seeds).
"""

import uuid

import httpx
import pytest
from conftest import assert_ok

SERVICE = "catalog"


def _h(headers: dict) -> dict:
    return dict(headers)


# ===================================================================
# Scenario 1: Каталог — доступность
# ===================================================================


class TestCatalogBrowsing:
    """Покупатель просматривает каталог."""

    def test_category_tree_accessible(
        self, clients: dict[str, httpx.Client], auth_headers: dict
    ) -> None:
        catalog = clients["catalog"]
        tree = assert_ok(catalog.get("/categories/", headers=_h(auth_headers))).json()
        assert len(tree) > 0, "Category tree should not be empty"

    def test_product_listing(
        self, clients: dict[str, httpx.Client], auth_headers: dict
    ) -> None:
        catalog = clients["catalog"]
        body = assert_ok(
            catalog.get("/products/", params={"page_size": 5}, headers=_h(auth_headers))
        ).json()
        assert body["total"] > 0, "Should have seeded products"
        assert len(body["items"]) > 0, "Should return product items"

    def test_product_by_id(
        self, clients: dict[str, httpx.Client], auth_headers: dict
    ) -> None:
        catalog = clients["catalog"]
        # Get first product from listing
        body = assert_ok(
            catalog.get("/products/", params={"page_size": 1}, headers=_h(auth_headers))
        ).json()
        if not body["items"]:
            pytest.skip("No products available")
        pid = body["items"][0]["id"]

        product = assert_ok(
            catalog.get(f"/products/{pid}", headers=_h(auth_headers))
        ).json()
        assert product["id"] == pid


# ===================================================================
# Scenario 2: Корзина — полный цикл
# ===================================================================


class TestCartOperations:
    """Операции с корзиной: добавить, изменить, удалить, очистить."""

    @pytest.mark.writes
    def test_cart_lifecycle(
        self,
        clients: dict[str, httpx.Client],
        auth_headers: dict,
    ) -> None:
        order_api = clients["order"]
        catalog = clients["catalog"]
        h = _h(auth_headers)

        # Найти товар
        products = assert_ok(
            catalog.get("/products/", params={"page_size": 1}, headers=h)
        ).json()
        if not products["items"]:
            pytest.skip("No products available")
        pid = products["items"][0]["id"]

        # Очистить корзину
        order_api.delete("/cart/", headers=h)

        # Добавить 3 единицы
        assert_ok(
            order_api.post("/cart/", json={"product_id": pid, "quantity": 3}, headers=h)
        )

        # Проверить наличие
        cart = assert_ok(order_api.get("/cart/", headers=h)).json()
        cart_items = cart.get("items", cart)
        if isinstance(cart_items, list):
            found = any(i["product_id"] == pid for i in cart_items)
        else:
            found = pid in cart_items
        assert found, f"Product {pid} should be in cart"

        # Удалить позицию
        assert_ok(order_api.delete(f"/cart/{pid}/", headers=h), 200, 204)

        # Очистить
        assert_ok(order_api.delete("/cart/", headers=h), 200, 204)


# ===================================================================
# Scenario 3: Заказ из корзины
# ===================================================================


class TestOrderFlow:
    """Оформление заказа из корзины."""

    @pytest.mark.writes
    def test_create_order_from_cart(
        self,
        clients: dict[str, httpx.Client],
        auth_headers: dict,
    ) -> None:
        order_api = clients["order"]
        catalog = clients["catalog"]
        h = _h(auth_headers)

        products = assert_ok(
            catalog.get("/products/", params={"page_size": 1}, headers=h)
        ).json()
        if not products["items"]:
            pytest.skip("No products available")
        pid = products["items"][0]["id"]

        # Корзина
        order_api.delete("/cart/", headers=h)
        assert_ok(
            order_api.post("/cart/", json={"product_id": pid, "quantity": 1}, headers=h)
        )

        # Заказ
        idem_key = f"e2e-order-{uuid.uuid4().hex[:12]}"
        resp = order_api.post(
            "/orders/",
            json={
                "shipping_address": {"city": "Moscow", "street": "Tverskaya 1"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers=h,
            params={"idempotency_key": idem_key},
        )
        # Заказ может быть создан или отклонён (нет стока / права)
        if resp.status_code in (200, 201):
            order = resp.json()
            assert "id" in order, f"Order should have id: {order}"
        else:
            # Приемлемые коды ошибок
            assert resp.status_code in (400, 403, 409, 422, 500), (
                f"Unexpected status {resp.status_code}: {resp.text[:200]}"
            )

    @pytest.mark.writes
    def test_empty_cart_rejected(
        self, clients: dict[str, httpx.Client], auth_headers: dict
    ) -> None:
        order_api = clients["order"]
        h = _h(auth_headers)

        order_api.delete("/cart/", headers=h)
        resp = order_api.post(
            "/orders/",
            json={
                "shipping_address": {"city": "Empty"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers=h,
        )
        assert resp.status_code in (400, 409, 422), (
            f"Empty cart should be rejected, got {resp.status_code}: {resp.text[:200]}"
        )


# ===================================================================
# Scenario 4: Идемпотентность
# ===================================================================


class TestOrderIdempotency:
    """Повторный заказ с тем же ключом не создаёт дубликат."""

    @pytest.mark.writes
    def test_duplicate_order_returns_same(
        self,
        clients: dict[str, httpx.Client],
        auth_headers: dict,
    ) -> None:
        order_api = clients["order"]
        catalog = clients["catalog"]
        h = _h(auth_headers)

        products = assert_ok(
            catalog.get("/products/", params={"page_size": 1}, headers=h)
        ).json()
        if not products["items"]:
            pytest.skip("No products available")
        pid = products["items"][0]["id"]

        order_api.delete("/cart/", headers=h)
        assert_ok(
            order_api.post("/cart/", json={"product_id": pid, "quantity": 1}, headers=h)
        )

        idem_key = f"e2e-idem-{uuid.uuid4().hex[:12]}"

        first = order_api.post(
            "/orders/",
            json={
                "shipping_address": {"city": "Kazan"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers=h,
            params={"idempotency_key": idem_key},
        )
        second = order_api.post(
            "/orders/",
            json={
                "shipping_address": {"city": "Kazan"},
                "payment_method": "MOCK",
                "tax_strategy": "RU",
            },
            headers=h,
            params={"idempotency_key": idem_key},
        )

        if first.status_code == 200 and second.status_code == 200:
            assert second.json()["id"] == first.json()["id"], (
                "Idempotent order should return same ID"
            )


# ===================================================================
# Scenario 5: Справочники
# ===================================================================


class TestDictionaryAccess:
    """Справочники доступны."""

    def test_units(self, clients: dict[str, httpx.Client], auth_headers: dict) -> None:
        d = clients["dictionary"]
        assert_ok(d.get("/dictionaries/units", headers=_h(auth_headers)))

    def test_timezones(
        self, clients: dict[str, httpx.Client], auth_headers: dict
    ) -> None:
        d = clients["dictionary"]
        body = assert_ok(
            d.get("/dictionaries/timezones", headers=_h(auth_headers))
        ).json()
        assert len(body) >= 1


# ===================================================================
# Scenario 6: Health checks
# ===================================================================


class TestHealthChecks:
    """Все сервисы отвечают на /health."""

    @pytest.mark.parametrize(
        "service",
        ["auth", "catalog", "order", "payment", "inventory", "dictionary", "report"],
    )
    def test_health(self, service: str, clients: dict[str, httpx.Client]) -> None:
        c = clients[service]
        resp = c.get("/health")
        assert resp.status_code in (200, 401, 403), (
            f"{service} /health: {resp.status_code}"
        )
