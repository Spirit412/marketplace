import uuid as _uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryPropertyItem(BaseModel):
    property_id: str
    is_required: bool = False
    sort_order: int = 0

    @field_validator("property_id")
    @classmethod
    def _validate_property_id(cls, v: str) -> str:
        _uuid.UUID(v)
        return v


class CreateCategoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: str | None = None
    parent_id: str | None = None
    properties: list[CategoryPropertyItem] = Field(default_factory=list)

    @field_validator("parent_id")
    @classmethod
    def _validate_parent_id(cls, v: str | None) -> str | None:
        if v is not None:
            _uuid.UUID(v)
        return v


class UpdateCategoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    parent_id: str | None = None

    @field_validator("parent_id")
    @classmethod
    def _validate_parent_id(cls, v: str | None) -> str | None:
        if v is not None:
            _uuid.UUID(v)
        return v
