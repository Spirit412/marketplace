import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.depends import (
    _require_admin,
    _user_role_name,
    enforce_login_rate_limit,
    get_auth_service,
    get_service_session,
)
from src.engines.redis_client import get_redis_client
from src.schemes.request.auth import (
    BlockUserRequest,
    CheckAccessRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
)
from src.schemes.response.auth import (
    CheckAccessResponse,
    CheckCredentialsResponse,
    SessionResponse,
    TokenResponse,
    UserResponse,
)
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, summary="Register user")
async def register(
    request: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> UserResponse:
    """Register a new user with email and password."""
    user = await service.register(
        session=session,
        email=request.email,
        password=request.password,
    )
    response = UserResponse.model_validate(user)
    response.role = _user_role_name(user)
    return response


@router.post(
    "/login",
    dependencies=[Depends(enforce_login_rate_limit)],
    summary="Login",
)
async def login(
    login_request: LoginRequest,
    http_request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> TokenResponse:
    """Authenticate a user and return access and refresh tokens."""
    device_info = http_request.headers.get("User-Agent")
    ip_address = http_request.client.host if http_request.client else None

    _user, access_token, refresh_token = await service.login(
        session=session,
        email=login_request.email,
        password=login_request.password,
        device_info=device_info,
        ip_address=ip_address,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", summary="Refresh tokens")
async def refresh(
    refresh_request: RefreshRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> TokenResponse:
    """Refresh an expired access token using a valid refresh token."""
    access_token, refresh_token = await service.refresh(
        session=session,
        refresh_token_str=refresh_request.refresh_token,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/logout",
    status_code=204,
    response_model=None,
    summary="Logout",
)
async def logout(
    refresh_request: RefreshRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> None:
    """Revoke a refresh token to log out from the current session."""
    await service.logout(
        session=session,
        refresh_token=refresh_request.refresh_token,
    )


@router.post(
    "/logout-all",
    status_code=204,
    response_model=None,
    dependencies=[Depends(get_token_payload)],
    summary="Logout from all sessions",
)
async def logout_all(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> None:
    """Revoke all refresh tokens to log out from every session."""
    await service.logout_all(
        session=session,
        user_id=uuid.UUID(token_payload.user_id),
    )


@router.get(
    "/sessions",
    summary="List active sessions",
)
async def get_sessions(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> list[SessionResponse]:
    """List all active sessions for the authenticated user."""
    sessions = await service.get_sessions(
        session=session,
        user_id=uuid.UUID(token_payload.user_id),
    )
    return [SessionResponse.model_validate(s) for s in sessions]


@router.post(
    "/check_credentials",
    summary="Check credentials",
)
async def check_credentials(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> CheckCredentialsResponse:
    """Validate the token payload and return credential status."""
    credentials = await service.resolve_credentials(
        session, uuid.UUID(token_payload.user_id), token_payload.iat
    )
    return CheckCredentialsResponse(
        valid=True,
        user_id=token_payload.user_id,
        role=credentials.role_name,
        is_admin=credentials.is_admin,
    )


@router.post(
    "/check-access",
    summary="Check access",
)
async def check_access(
    body: CheckAccessRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> CheckAccessResponse:
    """Check whether a user has access to a given resource and action.

    Called by AuthMiddleware in every service on each request.
    Token is passed in the body — no Authorization header required.
    """
    allowed, user_id, role, is_admin = await service.check_access(
        session=session,
        token=body.token,
        method=body.method,
        path=body.path,
        application=body.application,
    )
    return CheckAccessResponse(
        allowed=allowed,
        user_id=user_id,
        role=role,
        is_admin=is_admin,
    )


@router.post(
    "/users/{user_id}/block",
    dependencies=[Depends(_require_admin)],
    summary="Block user",
)
async def block_user(
    user_id: uuid.UUID,
    block_request: BlockUserRequest,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> UserResponse:
    """Block a user account and record the reason and blocker."""
    user = await service.block_user(
        session=session,
        user_id=user_id,
        blocked_by=uuid.UUID(token_payload.user_id),
        reason=block_request.reason,
    )
    return UserResponse.model_validate(user)


@router.post(
    "/users/{user_id}/unblock",
    dependencies=[
        Depends(_require_admin),
    ],
    summary="Unblock user",
)
async def unblock_user(
    user_id: uuid.UUID,
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> UserResponse:
    """Unblock a previously blocked user account."""
    user = await service.unblock_user(
        session=session,
        user_id=user_id,
    )
    return UserResponse.model_validate(user)


@router.get("/rate-limit-status", summary="Get rate limit status")
async def rate_limit_status(request: Request) -> dict[str, object]:
    """Return the current rate limit count for the requesting IP."""
    redis_client = get_redis_client()
    ip_address = request.client.host if request.client else "unknown"
    key = f"{settings.REDIS_KEY_PREFIX}:rate_limit:{ip_address}"
    current = await redis_client.get(key)
    return {
        "ip": ip_address,
        "current_count": int(current) if current else 0,
    }
