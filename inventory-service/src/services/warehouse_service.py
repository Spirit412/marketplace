from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.datatype import uuid7
from src.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
)
from src.models.models import Warehouse
from src.repositories.warehouse_repo import WarehouseRepo
from src.schemes.request.inventory import WarehouseCreateRequest, WarehouseUpdateRequest
from src.schemes.response.inventory import WarehouseResponse


class WarehouseService:
    async def create(
        self,
        *,
        session: AsyncSession,
        request: WarehouseCreateRequest,
        seller_id: UUID,
    ) -> WarehouseResponse:
        warehouse_repo = WarehouseRepo()
        existing = await warehouse_repo.get_by_name_and_seller(
            session, request.name, seller_id
        )
        if existing is not None:
            raise ConflictError(
                f"Warehouse '{request.name}' already exists",
            )

        warehouse = Warehouse(
            id=uuid7(),
            seller_id=seller_id,
            name=request.name,
            address=request.address,
            timezone=request.timezone,
        )
        warehouse = await warehouse_repo.create(session, warehouse)
        return WarehouseResponse.model_validate(warehouse)

    async def list(
        self,
        *,
        session: AsyncSession,
        seller_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list[WarehouseResponse]:
        warehouse_repo = WarehouseRepo()
        warehouses, _ = await warehouse_repo.list_by_seller(
            session, seller_id, offset=offset, limit=limit
        )
        return [WarehouseResponse.model_validate(ware) for ware in warehouses]

    async def get(
        self, *, session: AsyncSession, warehouse_id: UUID, seller_id: UUID
    ) -> WarehouseResponse:
        warehouse_repo = WarehouseRepo()
        warehouse = await warehouse_repo.get_by_id(session, warehouse_id)
        if warehouse is None:
            raise NotFoundError("Warehouse not found")
        if warehouse.seller_id != seller_id:
            raise ForbiddenError("Access denied")
        return WarehouseResponse.model_validate(warehouse)

    async def update(
        self,
        *,
        session: AsyncSession,
        warehouse_id: UUID,
        request: WarehouseUpdateRequest,
        seller_id: UUID,
    ) -> WarehouseResponse:
        warehouse_repo = WarehouseRepo()
        warehouse = await warehouse_repo.get_by_id(session, warehouse_id)
        if warehouse is None:
            raise NotFoundError("Warehouse not found")
        if warehouse.seller_id != seller_id:
            raise ForbiddenError("Access denied")

        if request.name is not None:
            existing = await warehouse_repo.get_by_name_and_seller(
                session, request.name, seller_id
            )
            if existing is not None and existing.id != warehouse_id:
                raise ConflictError(
                    f"Warehouse '{request.name}' already exists",
                )
            warehouse.name = request.name

        if request.address is not None:
            warehouse.address = request.address
        if request.timezone is not None:
            warehouse.timezone = request.timezone

        warehouse = await warehouse_repo.update(session, warehouse)
        return WarehouseResponse.model_validate(warehouse)

    async def delete(
        self, *, session: AsyncSession, warehouse_id: UUID, seller_id: UUID
    ) -> None:
        warehouse_repo = WarehouseRepo()
        warehouse = await warehouse_repo.get_by_id(session, warehouse_id)
        if warehouse is None:
            raise NotFoundError("Warehouse not found")
        if warehouse.seller_id != seller_id:
            raise ForbiddenError("Access denied")

        result = await warehouse_repo.deactivate(session, warehouse_id)
        if result is None:
            raise ServiceUnavailableError("Failed to deactivate warehouse")
