from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreateQuerySetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    data: dict[str, Any] = Field(default_factory=dict)
    displayed_fields: dict[str, Any] = Field(default_factory=dict)
    tags: dict[str, Any] = Field(default_factory=dict)


class UpdateQuerySetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)
    data: dict[str, Any] | None = None
    displayed_fields: dict[str, Any] | None = None
    tags: dict[str, Any] | None = None
