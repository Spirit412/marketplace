import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StockItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int
    reserved: int
    available: int


class StockResponse(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int
    reserved: int
    available: int


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stock_item_id: uuid.UUID
    movement_type: str
    quantity: int
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    created_at: datetime


class WarehouseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seller_id: uuid.UUID
    name: str
    address: str | None = None
    timezone: str
    is_active: bool
    created_at: datetime
