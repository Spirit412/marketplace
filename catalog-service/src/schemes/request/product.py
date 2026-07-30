
import uuid as _uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.enums.product import ProductStatus


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: float = Field(ge=0.0)
    sku: str | None = Field(default=None, max_length=100)
    stock: int = Field(default=0, ge=0)
    category_id: str | None = None
    custom_properties_config: dict = Field(default_factory=dict)
    images: dict = Field(default_factory=dict)

    @field_validator("category_id")
    @classmethod
    def _validate_category_id(cls, v: str | None) -> str | None:
        if v is not None:
            _uuid.UUID(v)
        return v


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: float | None = Field(default=None, ge=0.0)
    sku: str | None = Field(default=None, max_length=100)
    stock: int | None = Field(default=None, ge=0)
    category_id: str | None = None
    custom_properties_config: dict | None = None
    images: dict | None = None
    is_active: bool | None = None
    status: str | None = None

    @field_validator("category_id")
    @classmethod
    def _validate_category_id(cls, v: str | None) -> str | None:
        if v is not None:
            _uuid.UUID(v)
        return v

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in {stat.value for stat in ProductStatus}:
            raise ValueError(f"Invalid status: {v}")
        return v


class ProductFilterParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort: str = Field(default="newest")
    search: str | None = None
    filters_set: str | None = None
    category_id: str | None = None
    seller_id: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    status: str | None = None

    @field_validator("category_id", "seller_id")
    @classmethod
    def _validate_uuid_fields(cls, v: str | None) -> str | None:
        if v is not None:
            _uuid.UUID(v)
        return v

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in {stat.value for stat in ProductStatus}:
            raise ValueError(f"Invalid status: {v}")
        return v
