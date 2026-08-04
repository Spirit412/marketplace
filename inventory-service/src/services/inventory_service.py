import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.engines.rabbitmq import get_broker
from src.engines.redis import acquire_stock_lock, get_redis_client, release_stock_lock
from src.enums.movement_type import MovementType
from src.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from src.models.models import StockMovement
from src.repositories.movement_repo import MovementRepo
from src.repositories.stock_repo import StockRepo
from src.schemes.request.inventory import (
    AdjustRequest,
    ReceiptRequest,
    ReleaseRequest,
    ReserveByProductRequest,
    ReserveRequest,
    ShipRequest,
    StockCheckByProductRequest,
    StockCheckRequest,
)
from src.schemes.response.inventory import LowStockItemResponse, StockResponse

logger = logging.getLogger(__name__)


class InventoryService:
    async def get_low_stock_items(
        self, *, session: AsyncSession, threshold: int
    ) -> list[LowStockItemResponse]:
        """Stock items at or below threshold — backs scheduler's alert job."""
        stock_repo = StockRepo()
        items = await stock_repo.list_low_stock(session, threshold)
        return [
            LowStockItemResponse(
                product_id=item.product_id,
                warehouse_id=item.warehouse_id,
                stock=item.available,
            )
            for item in items
        ]

    async def check_stock_by_product(
        self, *, session: AsyncSession, request: StockCheckByProductRequest
    ) -> StockResponse | None:
        """Find a warehouse with enough available stock for a product.

        Returns None if no single warehouse can satisfy the requested
        quantity — callers (e.g. order-service) don't track warehouses
        themselves, they just need to know "is this orderable" and, if so,
        which warehouse a subsequent reserve-by-product call will pick.
        """
        stock_repo = StockRepo()
        candidates = await stock_repo.list_by_product(session, request.product_id)
        for item in candidates:
            if item.available >= request.quantity:
                return StockResponse(
                    product_id=item.product_id,
                    warehouse_id=item.warehouse_id,
                    quantity=item.quantity,
                    reserved=item.reserved,
                    available=item.available,
                )
        return None

    async def reserve_by_product(
        self, *, session: AsyncSession, request: ReserveByProductRequest
    ) -> StockResponse:
        """Reserve stock for a product, picking the best-stocked warehouse.

        Delegates to reserve() once a warehouse is chosen, so locking,
        atomic update, movement audit, and event publishing stay identical
        to a warehouse-scoped reservation.
        """
        stock_repo = StockRepo()
        candidates = await stock_repo.list_by_product(session, request.product_id)
        for item in candidates:
            if item.available >= request.quantity:
                return await self.reserve(
                    session=session,
                    request=ReserveRequest(
                        product_id=request.product_id,
                        warehouse_id=item.warehouse_id,
                        quantity=request.quantity,
                        reference_type=request.reference_type,
                        reference_id=request.reference_id,
                    ),
                )
        msg = (
            f"Insufficient stock for product {request.product_id}: "
            f"no single warehouse has {request.quantity} available"
        )
        raise ConflictError(msg)

    async def check_stock(
        self, *, session: AsyncSession, request: StockCheckRequest
    ) -> StockResponse:
        """Check available stock for a product in a warehouse."""
        stock_repo = StockRepo()
        item = await stock_repo.get_by_product_and_warehouse(
            session, request.product_id, request.warehouse_id
        )
        if item is None:
            return StockResponse(
                product_id=request.product_id,
                warehouse_id=request.warehouse_id,
                quantity=0,
                reserved=0,
                available=0,
            )
        return StockResponse(
            product_id=item.product_id,
            warehouse_id=item.warehouse_id,
            quantity=item.quantity,
            reserved=item.reserved,
            available=item.available,
        )

    async def reserve(
        self, *, session: AsyncSession, request: ReserveRequest
    ) -> StockResponse:
        """Reserve stock for an order. Uses Redis lock to prevent race conditions."""
        redis_client = get_redis_client()
        stock_repo = StockRepo()
        movement_repo = MovementRepo()

        acquired = await acquire_stock_lock(
            redis_client,
            str(request.product_id),
            str(request.warehouse_id),
        )
        if not acquired:
            raise ConflictError("Stock operation in progress, retry")

        try:
            item = await stock_repo.get_or_create(
                session, request.product_id, request.warehouse_id
            )

            available = item.quantity - item.reserved
            if available < request.quantity:
                try:
                    broker = get_broker()
                    await broker.publish(
                        {
                            "order_id": str(request.reference_id or ""),
                            "product_id": str(request.product_id),
                            "warehouse_id": str(request.warehouse_id),
                            "requested_quantity": request.quantity,
                            "available_quantity": available,
                        },
                        routing_key="stock.insufficient",
                    )
                except Exception:
                    logger.exception("Failed to publish stock.insufficient")
                msg = (
                    f"Insufficient stock: requested {request.quantity}, "
                    f"available {available}"
                )
                raise ConflictError(msg)

            updated = await stock_repo.update_quantity(
                session,
                item.id,
                reserved_delta=request.quantity,
            )
            if updated is None:
                raise ServiceUnavailableError("Failed to update stock")

            movement = StockMovement(
                stock_item_id=item.id,
                movement_type=MovementType.RESERVE.value,
                quantity=request.quantity,
                reference_type=request.reference_type,
                reference_id=request.reference_id,
            )
            await movement_repo.create(session, movement)

            # See StockRepo.commit()'s docstring for why this has to happen
            # here, ahead of the lock release in `finally` below.
            await stock_repo.commit(session)

            try:
                broker = get_broker()
                await broker.publish(
                    {
                        "order_id": str(request.reference_id or ""),
                        "product_id": str(request.product_id),
                        "warehouse_id": str(request.warehouse_id),
                        "reserved_quantity": request.quantity,
                    },
                    routing_key="stock.reserved",
                )
            except Exception:
                logger.exception("Failed to publish stock.reserved")

            new_available = updated.quantity - updated.reserved
            if new_available == 0:
                try:
                    broker = get_broker()
                    await broker.publish(
                        {
                            "product_id": str(request.product_id),
                            "warehouse_id": str(request.warehouse_id),
                            "current_quantity": new_available,
                            "min_threshold": 0,
                        },
                        routing_key="stock.depleted",
                    )
                except Exception:
                    logger.exception("Failed to publish stock.depleted")

            return StockResponse(
                product_id=updated.product_id,
                warehouse_id=updated.warehouse_id,
                quantity=updated.quantity,
                reserved=updated.reserved,
                available=updated.available,
            )

        finally:
            await release_stock_lock(
                redis_client,
                str(request.product_id),
                str(request.warehouse_id),
            )

    async def release(
        self, *, session: AsyncSession, request: ReleaseRequest
    ) -> StockResponse:
        """Release previously reserved stock."""
        redis_client = get_redis_client()
        stock_repo = StockRepo()
        movement_repo = MovementRepo()

        acquired = await acquire_stock_lock(
            redis_client,
            str(request.product_id),
            str(request.warehouse_id),
        )
        if not acquired:
            raise ConflictError("Stock operation in progress, retry")

        try:
            item = await stock_repo.get_by_product_and_warehouse(
                session, request.product_id, request.warehouse_id
            )
            if item is None:
                raise NotFoundError("Stock item not found")

            if item.reserved < request.quantity:
                msg = (
                    f"Cannot release {request.quantity}: only {item.reserved} reserved"
                )
                raise ConflictError(msg)

            updated = await stock_repo.update_quantity(
                session,
                item.id,
                reserved_delta=-request.quantity,
            )
            if updated is None:
                raise ServiceUnavailableError("Failed to update stock")

            movement = StockMovement(
                stock_item_id=item.id,
                movement_type=MovementType.RELEASE.value,
                quantity=request.quantity,
                reference_type=request.reference_type,
                reference_id=request.reference_id,
            )
            await movement_repo.create(session, movement)

            # See StockRepo.commit()'s docstring for why this has to happen
            # here, ahead of the lock release in `finally` below.
            await stock_repo.commit(session)

            try:
                broker = get_broker()
                await broker.publish(
                    {
                        "order_id": str(request.reference_id or ""),
                        "product_id": str(request.product_id),
                        "warehouse_id": str(request.warehouse_id),
                        "quantity": request.quantity,
                    },
                    routing_key="stock.released",
                )
            except Exception:
                logger.exception("Failed to publish stock.released")

            return StockResponse(
                product_id=updated.product_id,
                warehouse_id=updated.warehouse_id,
                quantity=updated.quantity,
                reserved=updated.reserved,
                available=updated.available,
            )

        finally:
            await release_stock_lock(
                redis_client,
                str(request.product_id),
                str(request.warehouse_id),
            )

    async def receive(
        self, *, session: AsyncSession, request: ReceiptRequest
    ) -> StockResponse:
        """Receive stock into warehouse."""
        stock_repo = StockRepo()
        movement_repo = MovementRepo()

        item = await stock_repo.get_or_create(
            session, request.product_id, request.warehouse_id
        )

        updated = await stock_repo.update_quantity(
            session,
            item.id,
            quantity_delta=request.quantity,
        )
        if updated is None:
            raise ServiceUnavailableError("Failed to update stock")

        movement = StockMovement(
            stock_item_id=item.id,
            movement_type=MovementType.RECEIPT.value,
            quantity=request.quantity,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
        )
        await movement_repo.create(session, movement)

        try:
            broker = get_broker()
            await broker.publish(
                {
                    "product_id": str(request.product_id),
                    "warehouse_id": str(request.warehouse_id),
                    "movement_type": MovementType.RECEIPT.value,
                    "quantity": request.quantity,
                    "new_total": updated.quantity,
                    "new_reserved": updated.reserved,
                },
                routing_key="stock.changed",
            )
        except Exception:
            logger.exception("Failed to publish stock.changed (receipt)")

        return StockResponse(
            product_id=updated.product_id,
            warehouse_id=updated.warehouse_id,
            quantity=updated.quantity,
            reserved=updated.reserved,
            available=updated.available,
        )

    async def ship(
        self, *, session: AsyncSession, request: ShipRequest
    ) -> StockResponse:
        """Ship/dispatch stock from warehouse."""
        stock_repo = StockRepo()
        movement_repo = MovementRepo()

        item = await stock_repo.get_by_product_and_warehouse(
            session, request.product_id, request.warehouse_id
        )
        if item is None:
            raise NotFoundError("Stock item not found")

        if item.quantity < request.quantity:
            msg = (
                f"Insufficient stock: requested {request.quantity}, "
                f"have {item.quantity}"
            )
            raise ConflictError(msg)

        reserved_delta = 0
        if item.reserved >= request.quantity:
            reserved_delta = -request.quantity
        elif item.reserved > 0:
            reserved_delta = -item.reserved

        updated = await stock_repo.update_quantity(
            session,
            item.id,
            quantity_delta=-request.quantity,
            reserved_delta=reserved_delta,
        )
        if updated is None:
            raise ServiceUnavailableError("Failed to update stock")

        movement = StockMovement(
            stock_item_id=item.id,
            movement_type=MovementType.SHIPMENT.value,
            quantity=request.quantity,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
        )
        await movement_repo.create(session, movement)

        try:
            broker = get_broker()
            await broker.publish(
                {
                    "product_id": str(request.product_id),
                    "warehouse_id": str(request.warehouse_id),
                    "movement_type": MovementType.SHIPMENT.value,
                    "quantity": request.quantity,
                    "new_total": updated.quantity,
                    "new_reserved": updated.reserved,
                },
                routing_key="stock.changed",
            )
        except Exception:
            logger.exception("Failed to publish stock.changed (shipment)")

        return StockResponse(
            product_id=updated.product_id,
            warehouse_id=updated.warehouse_id,
            quantity=updated.quantity,
            reserved=updated.reserved,
            available=updated.available,
        )

    async def adjust(
        self, *, session: AsyncSession, request: AdjustRequest
    ) -> StockResponse:
        """Adjust stock quantity (inventory audit)."""
        stock_repo = StockRepo()
        movement_repo = MovementRepo()

        item = await stock_repo.get_or_create(
            session, request.product_id, request.warehouse_id
        )

        current_qty = item.quantity
        delta = request.quantity - current_qty

        updated = await stock_repo.update_quantity(
            session,
            item.id,
            quantity_delta=delta,
        )
        if updated is None:
            raise ServiceUnavailableError("Failed to update stock")

        movement = StockMovement(
            stock_item_id=item.id,
            movement_type=MovementType.ADJUSTMENT.value,
            quantity=abs(delta),
            reference_type=None,
            reference_id=None,
        )
        await movement_repo.create(session, movement)

        try:
            broker = get_broker()
            await broker.publish(
                {
                    "product_id": str(request.product_id),
                    "warehouse_id": str(request.warehouse_id),
                    "movement_type": MovementType.ADJUSTMENT.value,
                    "quantity": delta,
                    "new_total": updated.quantity,
                    "new_reserved": updated.reserved,
                },
                routing_key="stock.changed",
            )
        except Exception:
            logger.exception("Failed to publish stock.changed (adjustment)")

        return StockResponse(
            product_id=updated.product_id,
            warehouse_id=updated.warehouse_id,
            quantity=updated.quantity,
            reserved=updated.reserved,
            available=updated.available,
        )

    async def return_stock(
        self, *, session: AsyncSession, request: ReceiptRequest
    ) -> StockResponse:
        """Return stock to warehouse (same as receive but with RETURN movement type)."""
        stock_repo = StockRepo()
        movement_repo = MovementRepo()

        item = await stock_repo.get_or_create(
            session, request.product_id, request.warehouse_id
        )

        updated = await stock_repo.update_quantity(
            session,
            item.id,
            quantity_delta=request.quantity,
        )
        if updated is None:
            raise ServiceUnavailableError("Failed to update stock")

        movement = StockMovement(
            stock_item_id=item.id,
            movement_type=MovementType.RETURN.value,
            quantity=request.quantity,
            reference_type=request.reference_type,
            reference_id=request.reference_id,
        )
        await movement_repo.create(session, movement)

        return StockResponse(
            product_id=updated.product_id,
            warehouse_id=updated.warehouse_id,
            quantity=updated.quantity,
            reserved=updated.reserved,
            available=updated.available,
        )
