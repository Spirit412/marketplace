import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.access import ResolvedAccess
from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.depends import get_service_session
from src.exceptions import NotFoundError
from src.repositories.session_repository import SessionRepository
from src.repositories.user_access_repository import UserAccessRepository
from src.repositories.user_repository import UserRepository
from src.schemes.rbac import UserAccessAssignRequest, UserAccessResponse
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["user-access"])


@router.put(
    "/users/{user_id}/access",
    summary="Assign user access",
)
async def assign_user_access(
    user_id: uuid.UUID,
    body: UserAccessAssignRequest,
    session: Annotated[AsyncSession, Depends(get_service_session)],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
) -> UserAccessResponse:
    """Assign or update a user's role and additional permissions."""
    repo = UserAccessRepository()
    result = await repo.create_or_update(
        session,
        user_id=user_id,
        role_uuid=body.role_uuid,
        additional_permissions=body.additional_permissions,
    )
    return UserAccessResponse.model_validate(result)


@router.get(
    "/users/{user_id}/access",
    summary="Get user access",
)
async def get_user_access(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_service_session)],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
) -> UserAccessResponse:
    """Get the assigned role and permissions for a user."""
    repo = UserAccessRepository()
    result = await repo.get_by_user(session, user_id)
    if not result:
        msg = f"UserAccess for {user_id} not found"
        raise NotFoundError(msg)
    return UserAccessResponse.model_validate(result)


@router.get(
    "/users/{user_id}/permissions",
    summary="Get user permissions",
)
async def get_user_permissions(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_service_session)],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
) -> ResolvedAccess:
    """Get the resolved permissions for a user, including inherited role permissions."""
    auth_svc = AuthService(
        user_repo=UserRepository(),
        session_repo=SessionRepository(),
        settings=settings,
    )
    return await auth_svc.get_user_permissions(session, user_id)
