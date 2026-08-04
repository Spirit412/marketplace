from uuid import UUID

from pydantic import BaseModel


class StockReservedPayload(BaseModel):
    order_id: UUID
    product_id: UUID
    warehouse_id: UUID
    reserved_quantity: int


class StockReleasedPayload(BaseModel):
    order_id: UUID
    product_id: UUID
    warehouse_id: UUID
    quantity: int


class StockInsufficientPayload(BaseModel):
    order_id: UUID
    product_id: UUID
    warehouse_id: UUID
    requested_quantity: int
    available_quantity: int


class StockDepletedPayload(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    current_quantity: int
    min_threshold: int


class StockChangedPayload(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    movement_type: str
    quantity: int
    new_total: int
    new_reserved: int
