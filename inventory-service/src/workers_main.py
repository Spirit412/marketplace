"""FastStream worker entry point for inventory-service.

Subscribes to order.* and product.created events.
"""


from src.engines.rabbitmq import get_broker

broker = get_broker()


@broker.subscriber("order.created")
async def handle_order_created(payload: dict) -> None:
    """Reserve stock when an order is created."""
    import uuid

    from src.core.database import _get_session_factory
    from src.repositories.movement_repo import MovementRepo
    from src.repositories.stock_repo import StockRepo
    from src.schemes.request.inventory import ReserveRequest
    from src.services.inventory_service import InventoryService

    session_factory = _get_session_factory()
    async with session_factory() as session:
        stock_repo = StockRepo()
        movement_repo = MovementRepo()
        service = InventoryService(stock_repo, movement_repo)

        for item in payload.get("items", []):
            request = ReserveRequest(
                product_id=uuid.UUID(item["product_id"]),
                warehouse_id=uuid.UUID(item["warehouse_id"]),
                quantity=item["quantity"],
                reference_type="order",
                reference_id=uuid.UUID(payload["order_id"]),
            )
            try:
                await service.reserve(request)
            except Exception:
                pass


@broker.subscriber("order.confirmed")
async def handle_order_confirmed(payload: dict) -> None:
    """Ship stock when an order is confirmed."""
    import uuid

    from src.core.database import _get_session_factory
    from src.repositories.movement_repo import MovementRepo
    from src.repositories.stock_repo import StockRepo
    from src.schemes.request.inventory import ShipRequest
    from src.services.inventory_service import InventoryService

    session_factory = _get_session_factory()
    async with session_factory() as session:
        stock_repo = StockRepo()
        movement_repo = MovementRepo()
        service = InventoryService(stock_repo, movement_repo)

        for item in payload.get("items", []):
            request = ShipRequest(
                product_id=uuid.UUID(item["product_id"]),
                warehouse_id=uuid.UUID(item["warehouse_id"]),
                quantity=item["quantity"],
                reference_type="order",
                reference_id=uuid.UUID(payload["order_id"]),
            )
            await service.ship(request)


@broker.subscriber("order.cancelled")
async def handle_order_cancelled(payload: dict) -> None:
    """Release reserved stock when an order is cancelled."""
    import uuid

    from src.core.database import _get_session_factory
    from src.repositories.movement_repo import MovementRepo
    from src.repositories.stock_repo import StockRepo
    from src.schemes.request.inventory import ReleaseRequest
    from src.services.inventory_service import InventoryService

    session_factory = _get_session_factory()
    async with session_factory() as session:
        stock_repo = StockRepo()
        movement_repo = MovementRepo()
        service = InventoryService(stock_repo, movement_repo)

        for item in payload.get("items", []):
            request = ReleaseRequest(
                product_id=uuid.UUID(item["product_id"]),
                warehouse_id=uuid.UUID(item["warehouse_id"]),
                quantity=item["quantity"],
                reference_type="order",
                reference_id=uuid.UUID(payload["order_id"]),
            )
            await service.release(request)
