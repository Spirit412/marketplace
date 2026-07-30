"""Seed script — populates DB from JSON data files.

Idempotent: safe to run multiple times (upserts by unique keys).

Data files:
    seeds/data/permissions.json   — [{name, app_id, method, path}, ...]
    seeds/data/roles.json         — [{name, description, is_admin}, ...]
    seeds/data/groups.json        — [{name, description, permissions: [name, ...]}, ...]
    seeds/data/role_groups.json   — {role_name: [group_name, ...]}
    seeds/data/users.json         — [{email, password, role}, ...]

Usage:
    poetry run python -m src.seeds.rbac
"""

import asyncio
import json
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import ServiceSessionMaker
from src.repositories.group_repository import GroupRepository
from src.repositories.permission_repository import PermissionRepository
from src.repositories.role_repository import RoleRepository
from src.schemes.rbac import (
    GroupCreateRequest,
    GroupUpdateRequest,
    PermissionCreateRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
)
from src.services.auth_service import AuthService
from src.services.group_service import GroupService
from src.services.permission_service import PermissionService
from src.services.role_service import RoleService

DATA_DIR = Path(__file__).parent / "data"


def _load_json(name: str) -> list | dict:
    with open(DATA_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


async def seed_rbac(session: AsyncSession) -> None:
    """Populate DB from JSON data files. Idempotent."""

    role_repo = RoleRepository()
    perm_repo = PermissionRepository()
    group_repo = GroupRepository()

    role_svc = RoleService(role_repo)
    perm_svc = PermissionService(perm_repo)
    group_svc = GroupService(group_repo, perm_repo)

    print("[1/6] Permissions...")
    permissions_data: list[dict] = _load_json("permissions.json")
    perm_name_to_uuid: dict[str, uuid.UUID] = {}
    for entry in permissions_data:
        existing = await perm_repo.get_by(
            session, app_id=entry["app_id"], method=entry["method"], path=entry["path"]
        )
        if existing is None:
            result = await perm_svc.create(
                session,
                PermissionCreateRequest(
                    name=entry["name"],
                    app_id=entry["app_id"],
                    method=entry["method"],
                    path=entry["path"],
                ),
            )
            perm_name_to_uuid[entry["name"]] = result.uuid
        else:
            perm_name_to_uuid[entry["name"]] = existing.uuid
    print(f"  {len(perm_name_to_uuid)} permissions")

    print("[2/6] Groups...")
    groups_data: list[dict] = _load_json("groups.json")
    group_name_to_uuid: dict[str, uuid.UUID] = {}
    for entry in groups_data:
        existing = await group_repo.get_by(session, name=entry["name"])
        if existing is None:
            result = await group_svc.create(
                session,
                GroupCreateRequest(
                    name=entry["name"],
                    description=entry["description"],
                ),
            )
            group_name_to_uuid[entry["name"]] = result.uuid
        else:
            group_name_to_uuid[entry["name"]] = existing.uuid
    print(f"  {len(group_name_to_uuid)} groups")

    print("[3/6] Linking groups → permissions...")
    for entry in groups_data:
        group_uuid = group_name_to_uuid[entry["name"]]
        perm_uuids = [
            perm_name_to_uuid[p]
            for p in entry["permissions"]
            if p in perm_name_to_uuid
        ]
        await group_svc.update(
            session,
            group_uuid,
            GroupUpdateRequest(permission_uuids=perm_uuids),
        )
    print("  done")

    print("[4/6] Roles...")
    roles_data: list[dict] = _load_json("roles.json")
    role_name_to_uuid: dict[str, uuid.UUID] = {}
    for entry in roles_data:
        existing = await role_repo.get_by(session, name=entry["name"])
        if existing is None:
            result = await role_svc.create(
                session,
                RoleCreateRequest(
                    name=entry["name"],
                    description=entry.get("description"),
                    is_admin=entry.get("is_admin", False),
                ),
            )
            role_name_to_uuid[entry["name"]] = result.uuid
        else:
            role_name_to_uuid[entry["name"]] = existing.uuid
    print(f"  {len(role_name_to_uuid)} roles")

    print("[5/6] Linking roles → groups...")
    role_groups_data: dict[str, list[str]] = _load_json("role_groups.json")
    for role_name, group_names in role_groups_data.items():
        role_uuid = role_name_to_uuid.get(role_name)
        if role_uuid is None:
            continue
        gids = [
            group_name_to_uuid[g]
            for g in group_names
            if g in group_name_to_uuid
        ]
        await role_svc.update(
            session,
            role_uuid,
            RoleUpdateRequest(group_uuids=gids),
        )
    print("  done")

    print("[6/6] Users...")
    from src.config.settings import settings
    from src.engines.redis_client import get_redis_client
    from src.patterns.password_hasher import PasswordHasher
    from src.repositories.session_repository import SessionRepository
    from src.repositories.user_access_repository import UserAccessRepository
    from src.repositories.user_repository import UserRepository

    auth_svc = AuthService(
        user_repo=UserRepository(),
        session_repo=SessionRepository(),
        settings=settings,
        password_hasher=PasswordHasher(scheme=settings.PASSWORD_HASHER),
        redis_client=get_redis_client(),
        user_access_repo=UserAccessRepository(),
        role_repo=role_repo,
        group_repo=group_repo,
    )
    users_data: list[dict] = _load_json("users.json")
    for entry in users_data:
        existing = await auth_svc.user_repo.get_by_email(session, entry["email"])
        if existing is not None:
            role_uuid = role_name_to_uuid.get(entry["role"])
            if role_uuid:
                ua_repo = UserAccessRepository()
                await ua_repo.create_or_update(
                    session,
                    user_uuid=existing.id,
                    role_uuid=role_uuid,
                )
            continue

        user = await auth_svc.register(
            session=session,
            email=entry["email"],
            password=entry["password"],
        )
        role_uuid = role_name_to_uuid.get(entry["role"])
        if role_uuid:
            ua_repo = UserAccessRepository()
            await ua_repo.create_or_update(
                session,
                user_uuid=user.id,
                role_uuid=role_uuid,
            )
    print(f"  {len(users_data)} users")

    await session.commit()
    print("Seed complete.")




async def _main() -> None:
    async with ServiceSessionMaker() as session:
        await seed_rbac(session)


if __name__ == "__main__":
    asyncio.run(_main())
