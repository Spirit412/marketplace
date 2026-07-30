"""Test fixtures for notification-service."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import Settings, get_settings
from src.main import app
from src.models.notification import Base, Notification, Template
from src.core.datatype import uuid7


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    settings = get_settings()
    engine = create_async_engine(settings.POSTGRES_DSN, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def sample_template(db_session: AsyncSession) -> Template:
    template = Template(
        id=uuid7(),
        code="order.created",
        locale="ru",
        subject="Заказ #{{ order_id }} создан",
        body_template="Ваш заказ №{{ order_id }} на сумму {{ total }} ₽ создан.",
        channels=["email", "websocket"],
        is_active=True,
    )
    db_session.add(template)
    await db_session.flush()
    return template


@pytest.fixture
async def sample_notification(db_session: AsyncSession) -> Notification:
    notification = Notification(
        id=uuid7(),
        user_uuid=uuid7(),
        event_type="order.created",
        channel="email",
        notification_type="info",
        subject="Test subject",
        body="Test body",
        status="unread",
        created_at=datetime.now(UTC),
    )
    db_session.add(notification)
    await db_session.flush()
    return notification
