"""FastStream worker entry point for inventory-service.

Subscribes to order.* and product.created events.
"""

import contextlib
from typing import Any
from uuid import UUID

from src.core.database import _get_session_factory
from src.engines.rabbitmq import get_broker
from src.schemes.request.inventory import ReleaseRequest, ReserveRequest, ShipRequest
from src.services.inventory_service import InventoryService

broker = get_broker()


@broker.subscriber("order.created")
async def handle_order_created(payload: dict[str, Any]) -> None:
    """Reserve stock when an order is created."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        service = InventoryService()

        for item in payload.get("items", []):
            request = ReserveRequest(
                product_id=UUID(item["product_id"]),
                warehouse_id=UUID(item["warehouse_id"]),
                quantity=item["quantity"],
                reference_type="order",
                reference_id=UUID(payload["order_id"]),
            )
            with contextlib.suppress(Exception):
                await service.reserve(session=session, request=request)


@broker.subscriber("order.confirmed")
async def handle_order_confirmed(payload: dict[str, Any]) -> None:
    """Ship stock when an order is confirmed."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        service = InventoryService()

        for item in payload.get("items", []):
            request = ShipRequest(
                product_id=UUID(item["product_id"]),
                warehouse_id=UUID(item["warehouse_id"]),
                quantity=item["quantity"],
                reference_type="order",
                reference_id=UUID(payload["order_id"]),
            )
            await service.ship(session=session, request=request)


@broker.subscriber("order.cancelled")
async def handle_order_cancelled(payload: dict[str, Any]) -> None:
    """Release reserved stock when an order is cancelled."""
    session_factory = _get_session_factory()
    async with session_factory() as session:
        service = InventoryService()

        for item in payload.get("items", []):
            request = ReleaseRequest(
                product_id=UUID(item["product_id"]),
                warehouse_id=UUID(item["warehouse_id"]),
                quantity=item["quantity"],
                reference_type="order",
                reference_id=UUID(payload["order_id"]),
            )
            await service.release(session=session, request=request)
