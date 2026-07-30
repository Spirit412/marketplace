"""Unit of Work — nested transaction context manager for SQLAlchemy.

Ensures data consistency: outermost context commits, inner contexts flush.
On exception: rollback entire transaction.
"""


import logging
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class UnitOfWork:
    """Async Unit of Work for managing SQLAlchemy transactions with nesting.

    Usage:
        async with UnitOfWork(session) as uow_session:
            await repo.create(uow_session, entity)
            await other_repo.update(uow_session, other)
        # commit happens here (outermost context)
    """

    _DEPTH_KEY = "_uow_depth"
    _FAILED_KEY = "_uow_failed"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        depth = self._session.info.get(self._DEPTH_KEY, 0)
        self._session.info[self._DEPTH_KEY] = depth + 1
        return self._session

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        depth = self._session.info.get(self._DEPTH_KEY, 1) - 1
        self._session.info[self._DEPTH_KEY] = depth

        if exc_type is not None:
            self._session.info[self._FAILED_KEY] = True

        try:
            if self._session.info.get(self._FAILED_KEY):
                if depth == 0:
                    await self._session.rollback()
                    logger.error("Transaction rolled back: %s", exc_type)
            elif depth == 0:
                await self._session.commit()
            else:
                await self._session.flush()
        finally:
            if depth == 0:
                await self._session.close()
                self._session.info.pop(self._DEPTH_KEY, None)
                self._session.info.pop(self._FAILED_KEY, None)
