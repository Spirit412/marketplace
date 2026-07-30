
import uuid

from pydantic import BaseModel, ConfigDict, Field


class StockCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    warehouse_id: uuid.UUID


class ReserveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int = Field(gt=0)
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None


class ReleaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int = Field(gt=0)
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None


class StockCheckByProductRequest(BaseModel):
    """Check availability without knowing which warehouse holds the stock."""

    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class ReserveByProductRequest(BaseModel):
    """Reserve from whichever warehouse has enough stock — caller doesn't pick one."""

    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    quantity: int = Field(gt=0)
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None


class ReceiptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int = Field(gt=0)
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None


class ShipRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int = Field(gt=0)
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None


class AdjustRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: uuid.UUID
    warehouse_id: uuid.UUID
    quantity: int
    reason: str = Field(min_length=1, max_length=500)


class WarehouseCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    address: str | None = None
    timezone: str = "UTC"


class WarehouseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = None
    timezone: str | None = None
