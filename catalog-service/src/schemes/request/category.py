from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryPropertyItem(BaseModel):
    property_id: UUID
    is_required: bool = False
    sort_order: int = 0


class CreateCategoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None
    properties: list[CategoryPropertyItem] = Field(default_factory=list)


class UpdateCategoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    parent_id: UUID | None = None
