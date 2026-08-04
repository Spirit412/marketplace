from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import NotFoundError
from src.repositories.user_access_repository import UserAccessRepository
from src.schemes.rbac import UserAccessResponse


class UserAccessService:
    def __init__(self, repo: UserAccessRepository) -> None:
        self._repo = repo

    async def assign(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        role_id: UUID | None,
        additional_permissions: list[UUID],
    ) -> UserAccessResponse:
        result = await self._repo.create_or_update(
            session,
            user_id=user_id,
            role_id=role_id,
            additional_permissions=additional_permissions,
        )
        return UserAccessResponse.model_validate(result)

    async def get_by_user(
        self, session: AsyncSession, user_id: UUID
    ) -> UserAccessResponse:
        result = await self._repo.get_by_user(session, user_id)
        if not result:
            raise NotFoundError(f"UserAccess for {user_id} not found")
        return UserAccessResponse.model_validate(result)
