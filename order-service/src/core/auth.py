import secrets
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
    """Minimal JWT claims — identity only.

    Permissions are resolved server-side by auth-service on each request
    via POST /auth/check-access (see AuthMiddleware). The token carries
    just enough to identify the caller; everything else is looked up.
    """

    type: Literal["access", "refresh"]
    user_id: str
    jti: str
    iat: int | None = None
    exp: int | None = None


def create_access_token(
    user_id: str,
    secret_key: str,
    algorithm: str,
    *,
    expires_minutes: int = 15,
) -> str:
    """Issue a short-lived access token.

    Args:
        user_id: Subject of the token.
        secret_key: HMAC signing key.
        algorithm: JWT signing algorithm.
        expires_minutes: Lifetime of the token in minutes.

    Returns:
        The encoded JWT.
    """
    return _encode(
        token_type="access",  # noqa: S106 -- a type label, not a secret
        user_id=user_id,
        secret_key=secret_key,
        algorithm=algorithm,
        lifetime=timedelta(minutes=expires_minutes),
    )


def create_refresh_token(
    user_id: str,
    secret_key: str,
    algorithm: str,
    *,
    expires_days: int = 7,
) -> str:
    """Issue a long-lived refresh token.

    Args:
        user_id: Subject of the token.
        secret_key: HMAC signing key.
        algorithm: JWT signing algorithm.
        expires_days: Lifetime of the token in days.

    Returns:
        The encoded JWT.
    """
    return _encode(
        token_type="refresh",  # noqa: S106 -- a type label, not a secret
        user_id=user_id,
        secret_key=secret_key,
        algorithm=algorithm,
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
    user_id: str,
    secret_key: str,
    algorithm: str,
    lifetime: timedelta,
) -> str:
    """Build and sign a token of the given type."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "type": token_type,
        "user_id": user_id,
        "jti": _generate_jti(),
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    encoded: str = jwt.encode(payload, secret_key, algorithm=algorithm)
    return encoded


def _generate_jti() -> str:
    """Return a random unique token identifier."""
    return secrets.token_hex(16)
