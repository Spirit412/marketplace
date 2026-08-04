from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.access import ResolvedAccess
from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.depends import Inject, get_auth_service, get_service_session
from src.schemes.rbac import UserAccessAssignRequest, UserAccessResponse
from src.services.auth_service import AuthService
from src.services.user_access_service import UserAccessService

router = APIRouter(prefix="/auth", tags=["user-access"])

UserIdPath = Annotated[
    UUID,
    Path(
        description="User id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000010"],
    ),
]


@router.put(
    "/users/{user_id}/access",
    summary="Assign user access",
)
async def assign_user_access(
    user_id: UserIdPath,
    body: UserAccessAssignRequest,
    service: Annotated[UserAccessService, Depends(Inject(UserAccessService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
) -> UserAccessResponse:
    """Assign or update a user's role and additional permissions."""
    return await service.assign(
        session,
        user_id=user_id,
        role_id=body.role_id,
        additional_permissions=body.additional_permissions,
    )


@router.get(
    "/users/{user_id}/access",
    summary="Get user access",
)
async def get_user_access(
    user_id: UserIdPath,
    service: Annotated[UserAccessService, Depends(Inject(UserAccessService))],
    session: Annotated[AsyncSession, Depends(get_service_session)],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
) -> UserAccessResponse:
    """Get the assigned role and permissions for a user."""
    return await service.get_by_user(session, user_id)


@router.get(
    "/users/{user_id}/permissions",
    summary="Get user permissions",
)
async def get_user_permissions(
    user_id: UserIdPath,
    auth_svc: Annotated[AuthService, Depends(get_auth_service)],
    session: Annotated[AsyncSession, Depends(get_service_session)],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
) -> ResolvedAccess:
    """Get the resolved permissions for a user, including inherited role permissions."""
    return await auth_svc.get_user_permissions(session, user_id)
