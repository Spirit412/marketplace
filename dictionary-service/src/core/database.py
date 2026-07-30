from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import get_settings

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine():
    """Return the process-wide async engine, creating it on first use.

    Built lazily so importing this module does not open sockets, which keeps
    Alembic and test collection independent of a reachable database.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            url=settings.postgres.dsn,
            echo=settings.postgres.ECHO,
            pool_size=settings.postgres.POOL_SIZE,
            max_overflow=settings.postgres.MAX_OVERFLOW,
            pool_recycle=settings.postgres.POOL_RECYCLE,
            pool_pre_ping=settings.postgres.POOL_PRE_PING,
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide session factory, creating it on first use."""
    global _session_factory
    if _session_factory is None:
        settings = get_settings()
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=settings.postgres.EXPIRE_ON_COMMIT,
            autoflush=settings.postgres.AUTO_FLUSH,
        )
    return _session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped session, committing on success.

    Rolls back and re-raises if the caller raises. Consumers that break out of
    the generator early skip the commit, so callers outside the request cycle
    should use the session factory directly and commit explicitly.
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
