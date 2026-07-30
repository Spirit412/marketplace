import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.auth import (
    Permission,
    TokenPayload,
    get_token_payload,
    require_permission,
)
from src.depends import (
    _require_admin,
    _user_role_name,
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


@router.post(
    "/register", response_model=UserResponse, status_code=201, summary="Register user"
)
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


@router.post("/login", response_model=TokenResponse, summary="Login")
async def login(
    login_request: LoginRequest,
    http_request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> TokenResponse:
    """Authenticate a user and return access and refresh tokens."""
    device_info = http_request.headers.get("User-Agent")
    ip_address = http_request.client.host if http_request.client else None

    user, access_token, refresh_token = await service.login(
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


@router.post("/refresh", response_model=TokenResponse, summary="Refresh tokens")
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
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
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
    dependencies=[
        Depends(require_permission(settings.APP_ID, Permission.WRITE)),
        Depends(get_token_payload),
    ],
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
        user_uuid=uuid.UUID(token_payload.user_uuid),
    )


@router.get(
    "/sessions",
    response_model=list[SessionResponse],
    summary="List active sessions",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_sessions(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> list[SessionResponse]:
    """List all active sessions for the authenticated user."""
    sessions = await service.get_sessions(
        session=session,
        user_uuid=uuid.UUID(token_payload.user_uuid),
    )
    return [SessionResponse.model_validate(s) for s in sessions]


@router.post(
    "/check_credentials",
    response_model=CheckCredentialsResponse,
    summary="Check credentials",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def check_credentials(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> CheckCredentialsResponse:
    """Validate the token payload and return credential status."""
    return CheckCredentialsResponse(
        valid=True,
        user_uuid=token_payload.user_uuid,
        role=token_payload.role,
        is_admin=token_payload.is_admin,
    )


@router.post(
    "/check-access",
    response_model=CheckAccessResponse,
    summary="Check access",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def check_access(
    body: CheckAccessRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
) -> CheckAccessResponse:
    """Check whether a user has access to a given resource and action."""
    allowed, user_uuid, role, is_admin = await service.check_access(
        session=session,
        token=body.token,
        method=body.method,
        path=body.path,
        application=body.application,
    )
    return CheckAccessResponse(
        allowed=allowed,
        user_uuid=user_uuid,
        role=role,
        is_admin=is_admin,
    )


@router.post(
    "/users/{user_id}/block",
    response_model=UserResponse,
    dependencies=[
        Depends(require_permission(settings.APP_ID, Permission.WRITE)),
        Depends(_require_admin),
    ],
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
        blocked_by=uuid.UUID(token_payload.user_uuid),
        reason=block_request.reason,
    )
    return UserResponse.model_validate(user)


@router.post(
    "/users/{user_id}/unblock",
    response_model=UserResponse,
    dependencies=[
        Depends(require_permission(settings.APP_ID, Permission.WRITE)),
        Depends(_require_admin),
    ],
    summary="Unblock user",
)
async def unblock_user(
    user_id: uuid.UUID,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
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
