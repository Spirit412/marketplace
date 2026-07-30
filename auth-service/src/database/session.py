from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import settings


class ServiceAsyncSession(AsyncSession):
    """Async SQLAlchemy session for auth-service database."""


engine = create_async_engine(
    url=settings.postgres.dsn,
    echo=settings.postgres.ECHO,
    pool_size=settings.postgres.POOL_SIZE,
    max_overflow=settings.postgres.MAX_OVERFLOW,
    pool_recycle=settings.postgres.POOL_RECYCLE,
    pool_pre_ping=settings.postgres.POOL_PRE_PING,
)

ServiceSessionMaker = async_sessionmaker(
    bind=engine,
    class_=ServiceAsyncSession,
    expire_on_commit=settings.postgres.EXPIRE_ON_COMMIT,
    autocommit=settings.postgres.AUTO_COMMIT,
    autoflush=settings.postgres.AUTO_FLUSH,
)
