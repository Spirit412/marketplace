
import uuid

from pydantic import BaseModel


class StockReservedPayload(BaseModel):
    order_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    reserved_quantity: int


class StockReleasedPayload(BaseModel):
    order_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int


class StockInsufficientPayload(BaseModel):
    order_id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    requested_quantity: int
    available_quantity: int


class StockDepletedPayload(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    current_quantity: int
    min_threshold: int


class StockChangedPayload(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    movement_type: str
    quantity: int
    new_total: int
    new_reserved: int
