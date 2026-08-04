from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 -- OAuth2 discriminator, not a secret


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: str
    role: str | None = None
    is_blocked: bool
    created_at: datetime


class SessionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID
    login_at: datetime
    logout_at: datetime | None
    refresh_count: int
    device_info: str | None
    ip_address: str | None


class CheckAccessResponse(BaseModel):
    allowed: bool
    user_id: UUID
    role: str | None = None
    is_admin: bool = False


class CheckCredentialsResponse(BaseModel):
    valid: bool
    user_id: UUID | None = None
    role: str | None = None
    is_admin: bool = False
    error: str | None = None
