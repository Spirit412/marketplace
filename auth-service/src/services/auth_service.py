import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import Settings
from src.core.access import ResolvedAccess
from src.core.auth import (
    Permission as AccessLevel,
)
from src.core.auth import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_jwt,
)
from src.core.datatype import uuid7
from src.engines.redis_client import get_redis_client
from src.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from src.models.permission import Permission
from src.models.user import SessionLog, User
from src.patterns.password_hasher import PasswordHasher
from src.repositories.group_repository import GroupRepository
from src.repositories.role_repository import RoleRepository
from src.repositories.session_repository import SessionRepository
from src.repositories.user_access_repository import UserAccessRepository
from src.repositories.user_repository import UserRepository


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
        settings: Settings,
        password_hasher: PasswordHasher | None = None,
        redis_client: Any = None,
        user_access_repo: UserAccessRepository | None = None,
        role_repo: RoleRepository | None = None,
        group_repo: GroupRepository | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._session_repo = session_repo
        self._settings = settings
        self._password_hasher = password_hasher or PasswordHasher(
            scheme=settings.PASSWORD_HASHER
        )
        self._user_access_repo = user_access_repo or UserAccessRepository()
        self._role_repo = role_repo or RoleRepository()
        self._group_repo = group_repo or GroupRepository()
        if redis_client is not None:
            self._redis: Any = redis_client
        else:
            self._redis = get_redis_client()

    @property
    def user_repo(self) -> UserRepository:
        return self._user_repo

    @property
    def session_repo(self) -> SessionRepository:
        return self._session_repo

    def _redis_key(self, *parts: str) -> str:
        """Build a namespaced Redis key: {prefix}:{part1}:{part2}:..."""
        return ":".join((self._settings.REDIS_KEY_PREFIX, *parts))

    def _user_tokens_key(self, user_uuid: str) -> str:
        """Redis Set tracking active refresh-token jti's for a user (avoids KEYS/SCAN in logout-all)."""
        return self._redis_key("user_tokens", user_uuid)

    @property
    def _token_ttl_seconds(self) -> int:
        """Refresh token TTL in seconds."""
        from datetime import timedelta

        return int(
            timedelta(days=self._settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds()
        )

    async def register(
        self,
        session: AsyncSession,
        email: str,
        password: str,
    ) -> User:
        existing = await self._user_repo.get_by_email(session, email)
        if existing:
            raise ConflictError("Email already registered")

        user = User(
            id=uuid7(),
            email=email,
            password_hash=self._password_hasher.hash(password),
        )
        created = await self._user_repo.create(session, user)

        default_role = await self._role_repo.get_by_name(
            session, self._settings.DEFAULT_ROLE_NAME
        )
        if default_role is not None:
            await self._user_access_repo.create_or_update(
                session,
                user_uuid=created.id,
                role_uuid=default_role.uuid,
            )

        result = await self._user_repo.get_with_access(session, created.id)
        return result if result is not None else created

    async def login(
        self,
        session: AsyncSession,
        email: str,
        password: str,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, str, str]:
        user = await self._user_repo.get_by_email(session, email)
        if not user:
            raise UnauthorizedError("Invalid credentials")

        if user.is_blocked:
            raise ForbiddenError(f"User blocked: {user.block_reason}")

        if not self._password_hasher.verify(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials")

        access_data = await self._resolve_permissions(session, user.id)

        permission_levels = self._permission_levels(access_data)

        access_token = create_access_token(
            str(user.id),
            self._settings.jwt.SECRET_KEY,
            self._settings.jwt.ALGORITHM,
            permissions=permission_levels,
            role=access_data.role_name,
            is_admin=access_data.is_admin,
            expires_minutes=self._settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        refresh_token = create_refresh_token(
            str(user.id),
            self._settings.jwt.SECRET_KEY,
            self._settings.jwt.ALGORITHM,
            expires_days=self._settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS,
        )

        refresh_payload = decode_jwt(
            refresh_token,
            self._settings.jwt.SECRET_KEY,
            self._settings.jwt.ALGORITHM,
        )

        session_log = SessionLog(
            id=uuid7(),
            user_uuid=user.id,
            device_info=device_info,
            ip_address=ip_address,
            session_jti=refresh_payload.jti,
        )
        await self._session_repo.create(session, session_log)

        await self._redis.setex(
            self._redis_key("refresh_token", str(user.id), refresh_payload.jti),
            self._token_ttl_seconds,
            "1",
        )
        await self._redis.sadd(self._user_tokens_key(str(user.id)), refresh_payload.jti)
        await self._redis.expire(
            self._user_tokens_key(str(user.id)), self._token_ttl_seconds
        )

        return user, access_token, refresh_token

    async def refresh(
        self,
        session: AsyncSession,
        refresh_token_str: str,
    ) -> tuple[str, str]:
        try:
            payload = decode_jwt(
                refresh_token_str,
                self._settings.jwt.SECRET_KEY,
                self._settings.jwt.ALGORITHM,
            )
        except Exception:
            raise UnauthorizedError("Invalid refresh token")

        if payload.type != "refresh":
            raise UnauthorizedError("Not a refresh token")

        invalidated_at = await self._redis.get(
            self._redis_key("token_invalidated_at", payload.user_uuid)
        )
        if invalidated_at and payload.iat:
            invalidated_dt = datetime.fromisoformat(invalidated_at).replace(tzinfo=UTC)
            token_iat = datetime.fromtimestamp(payload.iat, tz=UTC)
            if token_iat < invalidated_dt:
                raise ForbiddenError("Token revoked (logout-all)")

        stored = await self._redis.get(
            self._redis_key("refresh_token", payload.user_uuid, payload.jti)
        )
        if not stored:
            raise UnauthorizedError("Refresh token revoked")

        user = await self._user_repo.get_by_id(session, uuid.UUID(payload.user_uuid))
        if not user or user.is_blocked:
            raise ForbiddenError("User blocked or not found")

        access_data = await self._resolve_permissions(session, user.id)

        new_access = create_access_token(
            str(user.id),
            self._settings.jwt.SECRET_KEY,
            self._settings.jwt.ALGORITHM,
            permissions=self._permission_levels(access_data),
            role=access_data.role_name,
            is_admin=access_data.is_admin,
            expires_minutes=self._settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        new_refresh = create_refresh_token(
            str(user.id),
            self._settings.jwt.SECRET_KEY,
            self._settings.jwt.ALGORITHM,
            expires_days=self._settings.jwt.REFRESH_TOKEN_EXPIRE_DAYS,
        )

        new_payload = decode_jwt(
            new_refresh,
            self._settings.jwt.SECRET_KEY,
            self._settings.jwt.ALGORITHM,
        )

        await self._redis.delete(
            self._redis_key("refresh_token", payload.user_uuid, payload.jti)
        )
        await self._redis.srem(self._user_tokens_key(payload.user_uuid), payload.jti)

        await self._redis.setex(
            self._redis_key("refresh_token", str(user.id), new_payload.jti),
            self._token_ttl_seconds,
            "1",
        )
        await self._redis.sadd(self._user_tokens_key(str(user.id)), new_payload.jti)
        await self._redis.expire(
            self._user_tokens_key(str(user.id)), self._token_ttl_seconds
        )

        session_log = await self._session_repo.get_by_jti(session, payload.jti)
        if session_log is not None:
            session_log.refresh_count += 1
            await self._session_repo.update(session, session_log)

        return new_access, new_refresh

    async def logout(self, session: AsyncSession, refresh_token: str) -> None:
        try:
            payload = decode_jwt(
                refresh_token,
                self._settings.jwt.SECRET_KEY,
                self._settings.jwt.ALGORITHM,
            )
        except Exception:
            return

        await self._redis.delete(
            self._redis_key("refresh_token", payload.user_uuid, payload.jti)
        )
        await self._redis.srem(self._user_tokens_key(payload.user_uuid), payload.jti)
        await self._session_repo.close_session(session, payload.jti)

    async def logout_all(self, session: AsyncSession, user_uuid: uuid.UUID) -> None:
        await self._session_repo.close_all_for_user(session, user_uuid)

        tokens_key = self._user_tokens_key(str(user_uuid))
        jtis = await self._redis.smembers(tokens_key)
        if jtis:
            token_keys = [
                self._redis_key("refresh_token", str(user_uuid), jti) for jti in jtis
            ]
            await self._redis.delete(*token_keys)
        await self._redis.delete(tokens_key)

        invalidated_at = datetime.now(UTC)
        await self._redis.set(
            self._redis_key("token_invalidated_at", str(user_uuid)),
            invalidated_at.isoformat(),
            ex=self._token_ttl_seconds,
        )

    async def get_sessions(
        self, session: AsyncSession, user_uuid: uuid.UUID
    ) -> list[SessionLog]:
        return await self._session_repo.get_active_for_user(session, user_uuid)

    async def block_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        blocked_by: uuid.UUID,
        reason: str,
    ) -> User:
        user = await self._user_repo.get_by_id(session, user_id)
        if not user:
            raise NotFoundError("User not found")

        blocked = await self._user_repo.block(session, user_id, blocked_by, reason)
        if not blocked:
            raise NotFoundError("User not found")

        await self.logout_all(session, user_id)
        return blocked

    async def unblock_user(self, session: AsyncSession, user_id: uuid.UUID) -> User:
        user = await self._user_repo.unblock(session, user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def check_credentials(self, token: str) -> TokenPayload:
        return decode_jwt(
            token,
            self._settings.jwt.SECRET_KEY,
            self._settings.jwt.ALGORITHM,
        )

    async def _resolve_permissions(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> ResolvedAccess:
        """Resolve effective permissions for a user.

        Returns ResolvedAccess with permissions dict + role metadata.
        Sources:
          1. Role → Groups → Permissions
          2. UserAccess.additional_permissions (directly attached UUIDs)
        """
        user_access = await self._user_access_repo.get_by_user(session, user_id)

        result: dict[str, dict[str, set[str]]] = {}
        role_name: str | None = None
        is_admin: bool = False

        if user_access is not None and user_access.role_uuid is not None:
            role_permissions = await self._group_repo.resolve_permissions_for_role(
                session, user_access.role_uuid
            )
            self._merge_permissions(result, role_permissions)
            if user_access.role is not None:
                role_name = user_access.role.name
                is_admin = user_access.role.is_admin

        if user_access is not None and user_access.additional_permissions:
            from src.repositories.permission_repository import PermissionRepository

            perm_repo = PermissionRepository()
            extra_perms = await perm_repo.check_by_uuids(
                session, set(user_access.additional_permissions)
            )
            self._merge_permissions(result, extra_perms)

        return ResolvedAccess(
            permissions={
                app: {method: sorted(paths) for method, paths in methods.items()}
                for app, methods in result.items()
            },
            role_name=role_name,
            is_admin=is_admin,
        )

    @staticmethod
    def _merge_permissions(
        target: dict[str, dict[str, set[str]]],
        permissions: list[Permission],
    ) -> None:
        for perm in permissions:
            app_methods = target.setdefault(perm.app_id, {})
            app_methods.setdefault(perm.method, set()).add(perm.path)

    @staticmethod
    def _permission_levels(access: ResolvedAccess) -> dict[str, int]:
        """Collapse method/path permissions into a per-application level.

        Consuming services authorise with `require_permission(app_id, level)`,
        so the fine-grained {app: {method: [paths]}} map resolved from RBAC is
        reduced to the highest level each application grants. Admin roles get
        the maximum level for every application they touch.

        Args:
            access: Permissions resolved from the user's role and overrides.

        Returns:
            Application id mapped to the granted AccessLevel value.
        """
        method_levels = {
            "GET": AccessLevel.READ,
            "HEAD": AccessLevel.READ,
            "OPTIONS": AccessLevel.READ,
            "POST": AccessLevel.WRITE,
            "PUT": AccessLevel.WRITE,
            "PATCH": AccessLevel.WRITE,
            "DELETE": AccessLevel.ALL,
        }
        levels: dict[str, int] = {}
        for app_id, methods in access.permissions.items():
            if access.is_admin:
                levels[app_id] = int(AccessLevel.ALL)
                continue
            granted = [
                int(method_levels.get(method.upper(), AccessLevel.READ))
                for method in methods
            ]
            levels[app_id] = max(granted) if granted else int(AccessLevel.READ)
        return levels

    async def check_access(
        self,
        session: AsyncSession,
        token: str,
        method: str,
        path: str,
        application: str,
    ) -> tuple[bool, str, str | None, bool]:
        """Check if the token bearer can access (application, method, path).

        Returns: (allowed, user_uuid, role, is_admin)
        """
        import fnmatch

        payload = await self.check_credentials(token)
        user_id = uuid.UUID(payload.user_uuid)
        access = await self._resolve_permissions(session, user_id)
        app_perms = access.permissions.get(application, {})

        patterns = app_perms.get(method, [])
        allowed = any(fnmatch.fnmatch(path, p) for p in patterns)

        return allowed, payload.user_uuid, access.role_name, access.is_admin

    async def assign_role(
        self,
        session: AsyncSession,
        user_uuid: uuid.UUID,
        role_uuid: uuid.UUID | None,
        additional_permissions: list[uuid.UUID] | None = None,
    ) -> None:
        """Assign or update a role for a user."""
        user = await self._user_repo.get_by_id(session, user_uuid)
        if not user:
            raise NotFoundError("User not found")

        if role_uuid is not None:
            role = await self._role_repo.get_by_id(session, role_uuid)
            if not role:
                raise NotFoundError(f"Role {role_uuid} not found")

        await self._user_access_repo.create_or_update(
            session,
            user_uuid=user_uuid,
            role_uuid=role_uuid,
            additional_permissions=additional_permissions,
        )

    async def get_user_permissions(
        self, session: AsyncSession, user_uuid: uuid.UUID
    ) -> ResolvedAccess:
        """Get resolved permissions for any user (admin use)."""
        return await self._resolve_permissions(session, user_uuid)
