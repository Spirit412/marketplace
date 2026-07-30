from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from rodi import Container

from src.config.settings import Settings, settings
from src.core.auth import TokenPayload, get_token_payload
from src.database.session import ServiceAsyncSession, ServiceSessionMaker
from src.database.transaction import get_async_session
from src.engines.redis_client import get_redis_client
from src.patterns.password_hasher import PasswordHasher
from src.repositories.group_repository import GroupRepository
from src.repositories.permission_repository import PermissionRepository
from src.repositories.role_repository import RoleRepository
from src.repositories.session_repository import SessionRepository
from src.repositories.user_access_repository import UserAccessRepository
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.group_service import GroupService
from src.services.permission_service import PermissionService
from src.services.role_service import RoleService

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

    container.add_scoped(AuthService)


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


def _require_admin(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> TokenPayload:
    """Dependency: only admins pass."""
    from src.exceptions import ForbiddenError

    if not token_payload.is_admin:
        raise ForbiddenError("Admin access required")
    return token_payload
