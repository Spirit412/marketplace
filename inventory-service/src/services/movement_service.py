import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.enums.movement_type import MovementType
from src.models.models import StockMovement
from src.repositories.movement_repo import MovementRepo
from src.schemes.response.inventory import StockMovementResponse


class MovementService:
    async def record(
        self,
        *,
        session: AsyncSession,
        stock_item_id: uuid.UUID,
        movement_type: MovementType,
        quantity: int,
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
    ) -> StockMovement:
        movement_repo = MovementRepo()
        movement = StockMovement(
            stock_item_id=stock_item_id,
            movement_type=movement_type.value,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        return await movement_repo.create(session, movement)

    async def list_by_stock_item(
        self,
        *,
        session: AsyncSession,
        stock_item_id: uuid.UUID,
        movement_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[StockMovementResponse]:
        movement_repo = MovementRepo()
        movements = await movement_repo.list_by_stock_item(
            session,
            stock_item_id=stock_item_id,
            movement_type=movement_type,
            date_from=date_from,
            date_to=date_to,
            offset=offset,
            limit=limit,
        )
        return [StockMovementResponse.model_validate(move) for move in movements]

    async def list_by_warehouse(
        self,
        *,
        session: AsyncSession,
        warehouse_id: uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[StockMovementResponse]:
        movement_repo = MovementRepo()
        movements = await movement_repo.list_by_warehouse(
            session,
            warehouse_id=warehouse_id,
            offset=offset,
            limit=limit,
        )
        return [StockMovementResponse.model_validate(move) for move in movements]
