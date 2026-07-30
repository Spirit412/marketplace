"""Integration tests for stock endpoints."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from src.schemes.request.inventory import (
    ReserveRequest,
    StockCheckRequest,
)

pytestmark = pytest.mark.anyio


class TestStockEndpoints:
    async def test_check_stock_empty(self, async_client: AsyncClient) -> None:
        product_id = uuid.uuid4()
        warehouse_id = uuid.uuid4()
        response = await async_client.get(
            "/stock",
            params={"product_id": str(product_id), "warehouse_id": str(warehouse_id)},
        )
        assert response.status_code in (200, 403)

    async def test_reserve_requires_auth(self, async_client: AsyncClient) -> None:
        request = ReserveRequest(
            product_id=uuid.uuid4(),
            warehouse_id=uuid.uuid4(),
            quantity=5,
        )
        response = await async_client.post(
            "/stock/reserve",
            json=request.model_dump(mode="json"),
        )
        assert response.status_code == 403


class TestInventoryService:
    async def test_check_stock_nonexistent(self, db_session) -> None:
        from src.repositories.movement_repo import MovementRepo
        from src.repositories.stock_repo import StockRepo
        from src.services.inventory_service import InventoryService

        stock_repo = StockRepo(db_session)
        movement_repo = MovementRepo(db_session)
        service = InventoryService(stock_repo, movement_repo)

        product_id = uuid.uuid4()
        warehouse_id = uuid.uuid4()

        result = await service.check_stock(
            StockCheckRequest(product_id=product_id, warehouse_id=warehouse_id)
        )
        assert result.quantity == 0
        assert result.available == 0


class TestWarehouseModel:
    def test_warehouse_creation(self) -> None:
        from src.models.models import Warehouse

        warehouse = Warehouse(
            id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            name="Main Warehouse",
            timezone="Europe/Moscow",
        )
        assert warehouse.name == "Main Warehouse"
        assert warehouse.is_active is True
