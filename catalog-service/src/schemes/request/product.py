import uuid as _uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.enums.product import ProductStatus

# Pydantic-core's serializer treats sufficiently deep-but-non-circular JSON as
# a circular reference once it exceeds its internal recursion guard, crashing
# the *next* read of the row with 500 instead of rejecting the bad input up
# front. custom_properties_config/images are free-form client JSON with no
# other size limit, so cap nesting depth at write time.
_MAX_JSON_DEPTH = 20


def _check_json_depth(value: Any, *, depth: int = 0) -> None:
    if depth > _MAX_JSON_DEPTH:
        msg = f"exceeds maximum nesting depth of {_MAX_JSON_DEPTH}"
        raise ValueError(msg)
    if isinstance(value, dict):
        for item in value.values():
            _check_json_depth(item, depth=depth + 1)
    elif isinstance(value, list):
        for item in value:
            _check_json_depth(item, depth=depth + 1)


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    price: float = Field(ge=0.0)
    sku: str | None = Field(default=None, max_length=100)
    stock: int = Field(default=0, ge=0)
    category_id: str | None = None
    custom_properties_config: dict[str, Any] = Field(default_factory=dict)
    images: dict[str, Any] = Field(default_factory=dict)

    @field_validator("category_id")
    @classmethod
    def _validate_category_id(cls, v: str | None) -> str | None:
        if v is not None:
            _uuid.UUID(v)
        return v

    @field_validator("custom_properties_config", "images")
    @classmethod
    def _validate_json_depth(cls, v: dict[str, Any]) -> dict[str, Any]:
        _check_json_depth(v)
        return v


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: float | None = Field(default=None, ge=0.0)
    sku: str | None = Field(default=None, max_length=100)
    stock: int | None = Field(default=None, ge=0)
    category_id: str | None = None
    custom_properties_config: dict[str, Any] | None = None
    images: dict[str, Any] | None = None
    is_active: bool | None = None
    status: str | None = None

    @field_validator("category_id")
    @classmethod
    def _validate_category_id(cls, v: str | None) -> str | None:
        if v is not None:
            _uuid.UUID(v)
        return v

    @field_validator("custom_properties_config", "images")
    @classmethod
    def _validate_json_depth(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None:
            _check_json_depth(v)
        return v

    @field_validator("status")
    @classmethod
    def _validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in {stat.value for stat in ProductStatus}:
            msg = f"Invalid status: {v}"
            raise ValueError(msg)
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
            msg = f"Invalid status: {v}"
            raise ValueError(msg)
        return v
