import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import IntEnum
from typing import Annotated, Any, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from pydantic import BaseModel

from src.core.config import get_settings

oauth2_scheme_user = HTTPBearer()


class Permission(IntEnum):
    """Access level granted for an application, ordered least to most."""

    READ = 1
    WRITE = 2
    ALL = 3


class TokenPayload(BaseModel):
    """Claims carried by an access or refresh token.

    `permissions` maps an application id to the granted Permission level and
    is what `require_permission` checks. `role` and `is_admin` are carried for
    services that display or audit the issuing role; they are never used to
    grant access on their own.
    """

    type: Literal["access", "refresh"]
    user_uuid: str
    permissions: dict[str, int] = {}
    role: str | None = None
    is_admin: bool = False
    jti: str
    iat: int | None = None
    exp: int | None = None


def create_access_token(
    user_uuid: str,
    secret_key: str,
    algorithm: str,
    *,
    permissions: dict[str, int] | None = None,
    role: str | None = None,
    is_admin: bool = False,
    expires_minutes: int = 15,
) -> str:
    """Issue a short-lived access token.

    Args:
        user_uuid: Subject of the token.
        secret_key: HMAC signing key.
        algorithm: JWT signing algorithm.
        permissions: Application id to granted Permission level.
        role: Name of the role the permissions were resolved from.
        is_admin: Whether that role is an administrative one.
        expires_minutes: Lifetime of the token in minutes.

    Returns:
        The encoded JWT.
    """
    return _encode(
        token_type="access",
        user_uuid=user_uuid,
        secret_key=secret_key,
        algorithm=algorithm,
        permissions=permissions,
        role=role,
        is_admin=is_admin,
        lifetime=timedelta(minutes=expires_minutes),
    )


def create_refresh_token(
    user_uuid: str,
    secret_key: str,
    algorithm: str,
    *,
    permissions: dict[str, int] | None = None,
    role: str | None = None,
    is_admin: bool = False,
    expires_days: int = 7,
) -> str:
    """Issue a long-lived refresh token.

    Args:
        user_uuid: Subject of the token.
        secret_key: HMAC signing key.
        algorithm: JWT signing algorithm.
        permissions: Application id to granted Permission level.
        role: Name of the role the permissions were resolved from.
        is_admin: Whether that role is an administrative one.
        expires_days: Lifetime of the token in days.

    Returns:
        The encoded JWT.
    """
    return _encode(
        token_type="refresh",
        user_uuid=user_uuid,
        secret_key=secret_key,
        algorithm=algorithm,
        permissions=permissions,
        role=role,
        is_admin=is_admin,
        lifetime=timedelta(days=expires_days),
    )


def decode_jwt(
    token: str,
    secret_key: str,
    algorithm: str,
) -> TokenPayload:
    """Verify a token's signature and expiry and return its claims.

    Args:
        token: The encoded JWT.
        secret_key: HMAC signing key.
        algorithm: JWT signing algorithm.

    Returns:
        The decoded claims.

    Raises:
        HTTPException: 401 if the token is expired, malformed, or unsigned by
            this key.
    """
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={"require": ["exp"]},
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from exc
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    return TokenPayload.model_validate(payload)


def require_permission(
    application: str, required: Permission
) -> Callable[[TokenPayload], TokenPayload]:
    """Build a dependency asserting a permission level for an application.

    Args:
        application: Application id the permission is scoped to.
        required: Minimum level the caller must hold.

    Returns:
        A FastAPI dependency returning the validated token payload.
    """

    def dependency(
        token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    ) -> TokenPayload:
        granted = token_payload.permissions.get(application, 0)
        if granted < required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        return token_payload

    return dependency


def get_token_payload(
    token: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme_user)],
) -> TokenPayload:
    """Decode the bearer token on the current request."""
    settings = get_settings()
    return decode_jwt(
        token.credentials,
        settings.jwt.SECRET_KEY,
        settings.jwt.ALGORITHM,
    )


def _encode(
    *,
    token_type: Literal["access", "refresh"],
    user_uuid: str,
    secret_key: str,
    algorithm: str,
    permissions: dict[str, int] | None,
    role: str | None,
    is_admin: bool,
    lifetime: timedelta,
) -> str:
    """Build and sign a token of the given type."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "type": token_type,
        "user_uuid": user_uuid,
        "permissions": permissions or {},
        "role": role,
        "is_admin": is_admin,
        "jti": _generate_jti(),
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    encoded: str = jwt.encode(payload, secret_key, algorithm=algorithm)
    return encoded


def _generate_jti() -> str:
    """Return a random unique token identifier."""
    return secrets.token_hex(16)
