from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from rodi import Container

from src.config.settings import Settings, settings
from src.core.auth import TokenPayload, get_token_payload
from src.database.session import ServiceAsyncSession, ServiceSessionMaker
from src.database.transaction import get_async_session
from src.engines.redis_client import get_redis_client
from src.exceptions import ForbiddenError, RateLimitExceededError
from src.repositories.group_repository import GroupRepository
from src.repositories.permission_repository import PermissionRepository
from src.repositories.role_repository import RoleRepository
from src.repositories.session_repository import SessionRepository
from src.repositories.user_access_repository import UserAccessRepository
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.group_service import GroupService
from src.services.password_hasher import PasswordHasher
from src.services.permission_service import PermissionService
from src.services.rate_limit_service import RateLimitService
from src.services.role_service import RoleService
from src.services.user_access_service import UserAccessService

container = Container()


class Inject[T]:
    """FastAPI dependency that resolves a service from the rodi container."""

    __slots__ = ("_service",)

    def __init__(self, service: type[T]) -> None:
        self._service = service

    def __call__(self) -> T:
        return container.resolve(self._service)


def init_container() -> None:
    """Register all dependencies in the rodi container."""
    container.add_instance(settings, Settings)
    container.add_instance(get_redis_client())
    container.add_instance(
        PasswordHasher(scheme=settings.PASSWORD_HASHER), PasswordHasher
    )

    container.add_transient(UserRepository)
    container.add_transient(SessionRepository)
    container.add_transient(RoleRepository)
    container.add_transient(PermissionRepository)
    container.add_transient(GroupRepository)
    container.add_transient(UserAccessRepository)

    container.add_transient(RoleService)
    container.add_transient(PermissionService)
    container.add_transient(GroupService)
    container.add_transient(UserAccessService)

    container.add_scoped(RateLimitService)


async def get_service_session() -> AsyncGenerator[ServiceAsyncSession, None]:
    """FastAPI dependency: yield a per-request ServiceAsyncSession."""
    async with get_async_session(ServiceSessionMaker) as session:
        yield session


def _user_role_name(user: object) -> str | None:
    """Extract role name from user's UserAccess, if any."""
    accesses = getattr(user, "user_accesses", None) or []
    for ua in accesses:
        if ua.role is not None:
            name: str = ua.role.name
            return name
    return None


def get_auth_service() -> AuthService:
    return AuthService(
        user_repo=UserRepository(),
        session_repo=SessionRepository(),
        settings=settings,
        password_hasher=PasswordHasher(scheme=settings.PASSWORD_HASHER),
        redis_client=get_redis_client(),
    )


async def enforce_login_rate_limit(request: Request) -> None:
    """Dependency: throttle POST /auth/login attempts per client IP.

    Fixed-window counter in Redis, sharing the key format already read by
    GET /auth/rate-limit-status. Protects against credential-stuffing /
    brute-force login attempts; does not gate any other endpoint.
    """
    redis_client = get_redis_client()
    ip_address = request.client.host if request.client else "unknown"
    key = f"{settings.REDIS_KEY_PREFIX}:rate_limit:{ip_address}"

    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, settings.RATE_LIMIT_WINDOW_SECONDS)

    if count > settings.RATE_LIMIT_MAX_REQUESTS:
        message = f"Too many login attempts from {ip_address}, retry later"
        raise RateLimitExceededError(message)


async def _require_admin(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    session: Annotated[ServiceAsyncSession, Depends(get_service_session)],
) -> TokenPayload:
    """Dependency: only admins pass. Resolves role from DB, not JWT."""
    credentials = await get_auth_service().resolve_credentials(
        session, UUID(token_payload.user_id), token_payload.iat
    )
    if not credentials.is_admin:
        raise ForbiddenError("Admin access required")
    return token_payload
