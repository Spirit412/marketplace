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
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.database.session import ServiceSessionMaker
from src.engines.redis_client import get_redis_client
from src.repositories.group_repository import GroupRepository
from src.repositories.permission_repository import PermissionRepository
from src.repositories.role_repository import RoleRepository
from src.repositories.session_repository import SessionRepository
from src.repositories.user_access_repository import UserAccessRepository
from src.repositories.user_repository import UserRepository
from src.schemes.rbac import (
    GroupCreateRequest,
    GroupUpdateRequest,
    PermissionCreateRequest,
    RoleCreateRequest,
    RoleUpdateRequest,
)
from src.services.auth_service import AuthService
from src.services.group_service import GroupService
from src.services.password_hasher import PasswordHasher
from src.services.permission_service import PermissionService
from src.services.role_service import RoleService

if TYPE_CHECKING:
    import uuid

DATA_DIR = Path(__file__).parent / "data"


def _load_json(name: str) -> Any:
    """Load a seed data file.

    Returns `Any`: callers annotate the variable with the shape that
    specific file actually holds (a list of dicts, or a dict of lists).
    """
    with (DATA_DIR / name).open(encoding="utf-8") as fh:
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
    permissions_data: list[dict[str, Any]] = _load_json("permissions.json")
    perm_name_to_id: dict[str, uuid.UUID] = {}
    for entry in permissions_data:
        existing_permission = await perm_repo.get_by(
            session, app_id=entry["app_id"], method=entry["method"], path=entry["path"]
        )
        if existing_permission is None:
            created_permission = await perm_svc.create(
                session,
                PermissionCreateRequest(
                    name=entry["name"],
                    app_id=entry["app_id"],
                    method=entry["method"],
                    path=entry["path"],
                ),
            )
            perm_name_to_id[entry["name"]] = created_permission.id
        else:
            perm_name_to_id[entry["name"]] = existing_permission.id
    print(f"  {len(perm_name_to_id)} permissions")

    print("[2/6] Groups...")
    groups_data: list[dict[str, Any]] = _load_json("groups.json")
    group_name_to_id: dict[str, uuid.UUID] = {}
    for entry in groups_data:
        existing_group = await group_repo.get_by(session, name=entry["name"])
        if existing_group is None:
            created_group = await group_svc.create(
                session,
                GroupCreateRequest(
                    name=entry["name"],
                    description=entry["description"],
                ),
            )
            group_name_to_id[entry["name"]] = created_group.id
        else:
            group_name_to_id[entry["name"]] = existing_group.id
    print(f"  {len(group_name_to_id)} groups")

    print("[3/6] Linking groups → permissions...")
    for entry in groups_data:
        group_id = group_name_to_id[entry["name"]]
        perm_ids = [
            perm_name_to_id[p] for p in entry["permissions"] if p in perm_name_to_id
        ]
        await group_svc.update(
            session,
            group_id,
            GroupUpdateRequest(permission_ids=perm_ids),
        )
    print("  done")

    print("[4/6] Roles...")
    roles_data: list[dict[str, Any]] = _load_json("roles.json")
    role_name_to_id: dict[str, uuid.UUID] = {}
    for entry in roles_data:
        existing_role = await role_repo.get_by(session, name=entry["name"])
        if existing_role is None:
            created_role = await role_svc.create(
                session,
                RoleCreateRequest(
                    name=entry["name"],
                    description=entry.get("description"),
                    is_admin=entry.get("is_admin", False),
                ),
            )
            role_name_to_id[entry["name"]] = created_role.id
        else:
            role_name_to_id[entry["name"]] = existing_role.id
    print(f"  {len(role_name_to_id)} roles")

    print("[5/6] Linking roles → groups...")
    role_groups_data: dict[str, list[str]] = _load_json("role_groups.json")
    for role_name, group_names in role_groups_data.items():
        role_id = role_name_to_id.get(role_name)
        if role_id is None:
            continue
        gids = [group_name_to_id[g] for g in group_names if g in group_name_to_id]
        await role_svc.update(
            session,
            role_id,
            RoleUpdateRequest(group_ids=gids),
        )
    print("  done")

    print("[6/6] Users...")
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
    users_data: list[dict[str, Any]] = _load_json("users.json")
    for entry in users_data:
        existing_user = await auth_svc.user_repo.get_by_email(session, entry["email"])
        if existing_user is not None:
            role_id = role_name_to_id.get(entry["role"])
            if role_id:
                ua_repo = UserAccessRepository()
                await ua_repo.create_or_update(
                    session,
                    user_id=existing_user.id,
                    role_id=role_id,
                )
            continue

        user = await auth_svc.register(
            session=session,
            email=entry["email"],
            password=entry["password"],
        )
        role_id = role_name_to_id.get(entry["role"])
        if role_id:
            ua_repo = UserAccessRepository()
            await ua_repo.create_or_update(
                session,
                user_id=user.id,
                role_id=role_id,
            )
    print(f"  {len(users_data)} users")

    await session.commit()
    print("Seed complete.")


async def _main() -> None:
    async with ServiceSessionMaker() as session:
        await seed_rbac(session)


if __name__ == "__main__":
    asyncio.run(_main())
