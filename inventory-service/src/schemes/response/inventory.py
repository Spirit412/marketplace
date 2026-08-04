from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StockItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    warehouse_id: UUID
    quantity: int
    reserved: int
    available: int


class StockResponse(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    quantity: int
    reserved: int
    available: int


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    stock_item_id: UUID
    movement_type: str
    quantity: int
    reference_type: str | None = None
    reference_id: UUID | None = None
    created_at: datetime


class LowStockItemResponse(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    stock: int


class PopularProductResponse(BaseModel):
    product_id: UUID
    total_quantity: int


class WarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seller_id: UUID
    name: str
    address: str | None = None
    timezone: str
    is_active: bool
    created_at: datetime
