from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    is_admin: bool = False
    group_uuids: list[UUID] = Field(default_factory=list)


class RoleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    is_admin: bool | None = None
    group_uuids: list[UUID] | None = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str
    description: str | None
    is_admin: bool
    group_uuids: list[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class RoleListResponse(BaseModel):
    items: list[RoleResponse]
    total: int
    page: int
    pages: int


class PermissionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=256)
    app_id: str = Field(min_length=1, max_length=64)
    method: str = Field(min_length=1, max_length=10)
    path: str = Field(min_length=1, max_length=256)


class PermissionUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=256)
    app_id: str | None = Field(default=None, min_length=1, max_length=64)
    method: str | None = Field(default=None, min_length=1, max_length=10)
    path: str | None = Field(default=None, min_length=1, max_length=256)


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str
    app_id: str
    method: str
    path: str
    created_at: datetime
    updated_at: datetime


class PermissionListResponse(BaseModel):
    items: list[PermissionResponse]
    total: int
    page: int
    pages: int


class GroupCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    permission_uuids: list[UUID] = Field(default_factory=list)


class GroupUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    permission_uuids: list[UUID] | None = None


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str
    description: str | None
    permission_uuids: list[UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class GroupListResponse(BaseModel):
    items: list[GroupResponse]
    total: int
    page: int
    pages: int


class UserAccessAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_uuid: UUID | None = None
    additional_permissions: list[UUID] = Field(default_factory=list)


class UserAccessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_uuid: UUID
    role_uuid: UUID | None
    additional_permissions: list[UUID]
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    search: str | None = None
