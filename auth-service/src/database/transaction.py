import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_async_session[AS: AsyncSession](
    session_maker: async_sessionmaker[AS | Any],
) -> AsyncGenerator[AS, None]:
    """Provide an async SQLAlchemy session with automatic transaction handling.

    The session is committed on success, rolled back on error with logging.

    Args:
        session_maker: An async session factory used to create a new session.
    """
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Transaction rollback")
            raise


class UnitOfWork[AS: AsyncSession]:
    """Async Unit of Work for nested transaction support.

    Supports nested context managers — only the outermost
    context commits or rolls back; inner contexts flush.

    Usage:
        uow = UnitOfWork(session)
        async with uow:
            ...
    """

    DEPTH_KEY = "uow_depth"
    FAILED_KEY = "uow_failed"

    def __init__(self, session: AS) -> None:
        self.session = session

    async def __aenter__(self) -> AS:
        depth = self.session.info.get(self.DEPTH_KEY, 0)
        self.session.info[self.DEPTH_KEY] = depth + 1
        return self.session

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        depth = self.session.info.get(self.DEPTH_KEY, 1) - 1
        self.session.info[self.DEPTH_KEY] = depth

        if exc_type:
            self.session.info[self.FAILED_KEY] = True

        try:
            if self.session.info.get(self.FAILED_KEY):
                if depth == 0:
                    await self.session.rollback()
                    logger.error("Transaction rollback, exception %s", exc_type)
            elif depth == 0:
                await self.session.commit()
            else:
                await self.session.flush()

        finally:
            if depth == 0:
                await self.session.close()
                self.session.info.pop(self.FAILED_KEY, None)
