from datetime import datetime

from pydantic import BaseModel, field_validator


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


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
    user_uuid: str
    login_at: datetime
    logout_at: datetime | None
    refresh_count: int
    device_info: str | None
    ip_address: str | None

    @field_validator("id", "user_uuid", mode="before")
    @classmethod
    def _coerce_uuid(cls, v: object) -> str:
        return str(v)

    model_config = {"from_attributes": True}


class CheckAccessResponse(BaseModel):
    allowed: bool
    user_uuid: str
    role: str | None = None
    is_admin: bool = False


class CheckCredentialsResponse(BaseModel):
    valid: bool
    user_uuid: str | None = None
    role: str | None = None
    is_admin: bool = False
    error: str | None = None
