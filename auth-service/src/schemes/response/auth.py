from datetime import datetime

from pydantic import BaseModel, field_validator


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 -- OAuth2 discriminator, not a secret


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: str
    role: str | None = None
    is_blocked: bool
    created_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_uuid(cls, v: object) -> str:
        return str(v)


class SessionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    login_at: datetime
    logout_at: datetime | None
    refresh_count: int
    device_info: str | None
    ip_address: str | None

    @field_validator("id", "user_id", mode="before")
    @classmethod
    def _coerce_uuid(cls, v: object) -> str:
        return str(v)


class CheckAccessResponse(BaseModel):
    allowed: bool
    user_id: str
    role: str | None = None
    is_admin: bool = False


class CheckCredentialsResponse(BaseModel):
    valid: bool
    user_id: str | None = None
    role: str | None = None
    is_admin: bool = False
    error: str | None = None
