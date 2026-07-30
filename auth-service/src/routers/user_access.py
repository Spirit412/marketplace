import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.access import ResolvedAccess
from src.core.auth import Permission, TokenPayload, get_token_payload, require_permission
from src.depends import get_service_session
from src.repositories.user_access_repository import UserAccessRepository
from src.config.settings import settings
from src.repositories.session_repository import SessionRepository
from src.schemes.rbac import UserAccessAssignRequest, UserAccessResponse
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["user-access"])


@router.put("/users/{user_uuid}/access", response_model=UserAccessResponse, summary="Assign user access",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def assign_user_access(
    user_uuid: uuid.UUID,
    body: UserAccessAssignRequest,
    session: Annotated[AsyncSession, Depends(get_service_session)],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
) -> UserAccessResponse:
    """Assign or update a user's role and additional permissions."""
    repo = UserAccessRepository()
    result = await repo.create_or_update(
        session,
        user_uuid=user_uuid,
        role_uuid=body.role_uuid,
        additional_permissions=body.additional_permissions,
    )
    return UserAccessResponse.model_validate(result)


@router.get("/users/{user_uuid}/access", response_model=UserAccessResponse, summary="Get user access",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_user_access(
    user_uuid: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_service_session)],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
) -> UserAccessResponse:
    """Get the assigned role and permissions for a user."""
    repo = UserAccessRepository()
    result = await repo.get_by_user(session, user_uuid)
    if not result:
        from src.exceptions import NotFoundError

        raise NotFoundError(f"UserAccess for {user_uuid} not found")
    return UserAccessResponse.model_validate(result)


@router.get("/users/{user_uuid}/permissions", summary="Get user permissions",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_user_permissions(
    user_uuid: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_service_session)],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
) -> ResolvedAccess:
    """Get the resolved permissions for a user, including inherited role permissions."""

    auth_svc = AuthService(
        user_repo=UserRepository(),
        session_repo=SessionRepository(),
        settings=settings,
    )
    return await auth_svc.get_user_permissions(session, user_uuid)
