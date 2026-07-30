"""Shared auth middleware for all marketplace services.

Usage in any service:
    from src.auth_middleware import AuthMiddleware, get_current_user, check_access

    # Option A: FastAPI dependency (per-route)
    @router.get("/products")
    async def get_products(
        user: Annotated[TokenPayload, Depends(get_current_user)],
    ):
        ...

    # Option B: middleware (all routes)
    app.add_middleware(AuthMiddleware)

    # Option C: path-level check
    @router.post("/products")
    async def create_product(
        user: Annotated[TokenPayload, Depends(check_access("CATALOG", "POST", "/products"))],
    ):
        ...
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.auth import TokenPayload, decode_jwt

_JWT_SECRET: str | None = None
_JWT_ALGORITHM: str | None = None
_AUTH_SERVICE_URL: str | None = None
_APP_ID: str | None = None

oauth2_scheme = HTTPBearer()


def init_auth(
    *, jwt_secret: str, jwt_algorithm: str, auth_service_url: str, app_id: str
) -> None:
    """Initialize auth config for this service. Call once at startup."""
    global _JWT_SECRET, _JWT_ALGORITHM, _AUTH_SERVICE_URL, _APP_ID
    _JWT_SECRET = jwt_secret
    _JWT_ALGORITHM = jwt_algorithm
    _AUTH_SERVICE_URL = auth_service_url
    _APP_ID = app_id


def _get_secret_and_algo() -> tuple[str, str]:
    if _JWT_SECRET is None or _JWT_ALGORITHM is None:
        raise RuntimeError("Auth not initialized. Call init_auth() at startup.")
    return _JWT_SECRET, _JWT_ALGORITHM


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> TokenPayload:
    """FastAPI dependency: validate JWT, return payload.

    Raises 401 with 'token_expired' detail if token is expired (client should refresh).
    """
    secret, algo = _get_secret_and_algo()
    try:
        return decode_jwt(credentials.credentials, secret, algo)
    except HTTPException as exc:
        detail = str(exc.detail)
        if "expired" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "token_expired", "message": detail},
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_token", "message": detail},
        ) from exc


def check_access(
    method: str,
    path: str,
) -> "Callable":
    """FastAPI dependency: validate JWT + check path-level access via auth-service.

    Calls POST {auth_service_url}/auth/check-access.
    """
    import httpx

    def dependency(
        user: Annotated[TokenPayload, Depends(get_current_user)],
        request: Request,
    ) -> TokenPayload:
        if _AUTH_SERVICE_URL is None or _APP_ID is None:
            raise RuntimeError("Auth not initialized")

        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        try:
            resp = httpx.post(
                f"{_AUTH_SERVICE_URL}/auth/check-access",
                json={
                    "token": token,
                    "method": method,
                    "path": path,
                    "application": _APP_ID,
                },
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

        if not data.get("allowed"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return user

    return dependency


class AuthMiddleware(BaseHTTPMiddleware):
    """Global middleware: validates JWT on every request.

    Skips paths matching `exclude_paths`.
    Attaches `request.state.user` (TokenPayload) on success.
    Returns 401 with 'token_expired' on expired tokens.
    """

    def __init__(
        self,
        app: "object",
        exclude_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._exclude = set(
            exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"]
        )

    async def dispatch(self, request: Request, call_next: "Callable") -> JSONResponse:
        if request.url.path in self._exclude:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "missing_token"},
            )

        token = auth_header.removeprefix("Bearer ").strip()
        secret, algo = _get_secret_and_algo()
        try:
            payload = decode_jwt(token, secret, algo)
        except HTTPException as exc:
            detail = str(exc.detail)
            code = "token_expired" if "expired" in detail.lower() else "invalid_token"
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": code, "message": detail},
            )

        request.state.user = payload
        return await call_next(request)
