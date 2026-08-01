"""Shared auth middleware for all marketplace services.

Middleware calls auth-service on every request to check permissions.
Permissions are managed server-side in auth-service's RBAC database
(roles → groups → permissions), not hardcoded in router code.

Decisions are cached locally per-service in Redis for a short TTL
(CHECK_ACCESS_CACHE_TTL_SECONDS) keyed by a hash of (app_id, token, method,
path), so repeat requests for the same token/route skip both the network
hop to auth-service and its RBAC DB lookup. A revoked/changed permission
takes effect within the TTL window, not instantly — see
"Auth Service — Ролевая модель" §4.5 for the trade-off this accepts.

Usage:
    from src.auth_middleware import AuthMiddleware, init_auth

    # In main.py lifespan:
    init_auth(
        auth_service_url=...,
        app_id=...,
        redis_url=settings.redis.url,   # optional — omit to disable caching
    )

    # Add middleware:
    app.add_middleware(AuthMiddleware, exclude_paths=["/health", "/docs", ...])

    # After middleware, request.state holds:
    #   request.state._auth_state.user_id: str
    #   request.state._auth_state.role: str | None
    #   request.state._auth_state.is_admin: bool
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Any

import httpx
import redis.asyncio as redis_asyncio
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

_AUTH_SERVICE_URL: str | None = None
_APP_ID: str | None = None
_REDIS: redis_asyncio.Redis | None = None
_CACHE_TTL_SECONDS: int = 10


def init_auth(
    *,
    auth_service_url: str,
    app_id: str,
    redis_url: str | None = None,
    cache_ttl_seconds: int = 10,
) -> None:
    """Initialize auth config for this service. Call once at startup.

    redis_url is optional: without it every request hits auth-service over
    HTTP (no local caching). With it, check-access decisions are cached for
    cache_ttl_seconds. Uses its own connection, independent of any Redis
    client the service already has for its own purposes — this module stays
    self-contained (byte-identical across all 10 services) rather than
    importing each service's differently-named engines/redis*.py.
    """
    global _AUTH_SERVICE_URL, _APP_ID, _REDIS, _CACHE_TTL_SECONDS
    _AUTH_SERVICE_URL = auth_service_url
    _APP_ID = app_id
    _CACHE_TTL_SECONDS = cache_ttl_seconds
    _REDIS = (
        redis_asyncio.from_url(redis_url, decode_responses=True) if redis_url else None
    )


@dataclass(slots=True)
class _AuthState:
    """Credentials attached to request.state by the middleware."""

    user_id: str
    role: str | None
    is_admin: bool


def _get_auth_state(request: Request) -> _AuthState:
    """Retrieve the auth state set by AuthMiddleware."""
    if not hasattr(request.state, "_auth_state"):
        raise RuntimeError(
            "AuthMiddleware not active — add app.add_middleware(AuthMiddleware)"
        )
    # Starlette's State.__getattr__ returns Any regardless of what's
    # actually stored -- narrow it back to the type this function promises.
    auth_state: _AuthState = request.state._auth_state  # noqa: SLF001
    return auth_state


def _cache_key(token: str, method: str, path: str) -> str:
    """Hash (app_id, token, method, path) into a short, opaque Redis key.

    app_id is folded into the hash so all 10 services can share one flat
    Redis keyspace without a per-service prefix; hashing avoids storing the
    raw bearer token as (part of) a key name.
    """
    raw = f"{_APP_ID}:{token}:{method}:{path}"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"check_access:{digest}"


async def _get_cached_decision(key: str) -> dict[str, Any] | None:
    if _REDIS is None:
        return None
    try:
        raw = await _REDIS.get(key)
    except Exception:
        logger.warning("check-access cache read failed, falling back to auth-service")
        return None
    if raw is None:
        return None
    result: dict[str, Any] = json.loads(raw)
    return result


async def _set_cached_decision(key: str, data: dict[str, Any]) -> None:
    if _REDIS is None:
        return
    try:
        await _REDIS.setex(key, _CACHE_TTL_SECONDS, json.dumps(data))
    except Exception:
        logger.warning("check-access cache write failed, continuing uncached")


class AuthMiddleware(BaseHTTPMiddleware):
    """Calls auth-service /auth/check-access on every non-excluded request.

    Stores resolved credentials in request.state._auth_state.
    Returns 401 for missing/invalid tokens, 403 for access denied.
    """

    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._exclude = set(
            exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"]
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in self._exclude:
            return await call_next(request)

        if request.method not in ("GET", "POST", "PATCH", "PUT", "DELETE"):
            return await call_next(request)

        token: str | None = (
            request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        )
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "missing_token"},
            )

        if _AUTH_SERVICE_URL is None or _APP_ID is None:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "auth_not_initialized"},
            )

        cache_key = _cache_key(token, request.method, request.url.path)
        data = await _get_cached_decision(cache_key)

        if data is None:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(
                        f"{_AUTH_SERVICE_URL}/auth/check-access",
                        json={
                            "token": token,
                            "method": request.method,
                            "path": request.url.path,
                            "application": _APP_ID,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

            except httpx.ConnectError:
                logger.exception("Auth service unreachable at %s", _AUTH_SERVICE_URL)
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={"error": "auth_service_unreachable"},
                )
            except httpx.HTTPStatusError as exc:
                logger.warning("Auth check failed: %s", exc)
                return JSONResponse(
                    status_code=exc.response.status_code,
                    content={"error": "auth_failed"},
                )
            except Exception:
                logger.exception("Unexpected error during auth check")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"error": "auth_check_error"},
                )

            await _set_cached_decision(cache_key, data)

        if not data.get("allowed"):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "access_denied"},
            )

        request.state._auth_state = _AuthState(  # noqa: SLF001
            user_id=data["user_id"],
            role=data.get("role"),
            is_admin=data.get("is_admin", False),
        )

        return await call_next(request)
