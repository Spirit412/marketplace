from __future__ import annotations

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ImportUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> bool:
        if exc_type is not None:
            await self._session.rollback()
            return False
        await self._session.commit()
        return False
