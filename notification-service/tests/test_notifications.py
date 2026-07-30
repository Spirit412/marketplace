"""Tests for notification service."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.datatype import uuid7
from src.models.notification import Notification, Template
from src.patterns.frontend_notification_builder import FrontendNotificationBuilder
from src.patterns.notification_builder import NotificationBuilder
from src.repositories.notification_repo import NotificationRepository
from src.repositories.template_repo import TemplateRepository
from src.schemes.internal.notification import NotificationPayload
from src.schemes.ws_message import WSMessage


class TestNotificationBuilder:
    def test_build_renders_jinja2(self) -> None:
        template = Template(
            code="order.created",
            locale="ru",
            subject="Заказ #{{ order_id }}",
            body_template="Сумма: {{ total }} ₽",
        )
        builder = (
            NotificationBuilder()
            .with_template(template)
            .with_variables({"order_id": "123", "total": 5000})
            .with_recipient(uuid7())
            .with_channel("email")
            .with_event_type("order.created")
        )
        notification = builder.build()
        assert notification.subject == "Заказ #123"
        assert notification.body == "Сумма: 5000 ₽"
        assert notification.channel == "email"
        assert notification.event_type == "order.created"

    def test_build_without_template_raises(self) -> None:
        builder = NotificationBuilder()
        with pytest.raises(ValueError, match="Template is required"):
            builder.build()


class TestFrontendNotificationBuilder:
    def test_build_ws_message(self) -> None:
        builder = (
            FrontendNotificationBuilder()
            .with_event_type("order.confirmed")
            .with_notification_type("success")
            .with_title("Заказ подтверждён")
            .with_body("Ваш заказ #123 подтверждён продавцом.")
        )
        msg = builder.build()
        assert isinstance(msg, WSMessage)
        assert msg.type == "order.confirmed"
        assert msg.notification_type == "success"
        assert msg.title == "Заказ подтверждён"
        assert "подтверждён" in msg.body


class TestNotificationRepository:
    async def test_create_and_get(self, db_session: AsyncSession) -> None:
        repo = NotificationRepository(db_session)
        n = Notification(
            id=uuid7(),
            user_uuid=uuid7(),
            event_type="test.event",
            channel="email",
            notification_type="info",
            subject="Test",
            body="Test body",
            status="unread",
            created_at=datetime.now(UTC),
        )
        created = await repo.create(n)
        fetched = await repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.subject == "Test"

    async def test_get_unread(self, db_session: AsyncSession) -> None:
        repo = NotificationRepository(db_session)
        user = uuid7()
        n1 = Notification(
            id=uuid7(),
            user_uuid=user,
            event_type="e1",
            channel="email",
            notification_type="info",
            subject="S1",
            body="B1",
            status="unread",
            created_at=datetime.now(UTC),
        )
        n2 = Notification(
            id=uuid7(),
            user_uuid=user,
            event_type="e2",
            channel="email",
            notification_type="info",
            subject="S2",
            body="B2",
            status="read",
            created_at=datetime.now(UTC),
        )
        await repo.create(n1)
        await repo.create(n2)

        unread = await repo.get_unread(user)
        assert len(unread) == 1
        assert unread[0].id == n1.id

    async def test_mark_read(self, db_session: AsyncSession) -> None:
        repo = NotificationRepository(db_session)
        n = Notification(
            id=uuid7(),
            user_uuid=uuid7(),
            event_type="e1",
            channel="email",
            notification_type="info",
            subject="S",
            body="B",
            status="unread",
            created_at=datetime.now(UTC),
        )
        await repo.create(n)
        result = await repo.mark_read(n.id)
        assert result is not None
        assert result.status == "read"
        assert result.read_at is not None


class TestTemplateRepository:
    async def test_get_by_code_and_locale(self, db_session: AsyncSession) -> None:
        repo = TemplateRepository(db_session)
        tpl = Template(
            id=uuid7(),
            code="order.created",
            locale="ru",
            subject="Заказ создан",
            body_template="Тело",
            is_active=True,
        )
        await repo.create(tpl)

        found = await repo.get_by_code_and_locale("order.created", "ru")
        assert found is not None
        assert found.subject == "Заказ создан"

        not_found = await repo.get_by_code_and_locale("nonexistent", "ru")
        assert not_found is None

    async def test_inactive_not_returned(self, db_session: AsyncSession) -> None:
        repo = TemplateRepository(db_session)
        tpl = Template(
            id=uuid7(),
            code="old.event",
            locale="ru",
            subject="Old",
            body_template="Old",
            is_active=False,
        )
        await repo.create(tpl)
        found = await repo.get_by_code_and_locale("old.event", "ru")
        assert found is None


class TestNotificationPayload:
    def test_parse_from_dict(self) -> None:
        data = {
            "event_type": "order.created",
            "user_uuid": "00000000-0000-7000-8000-000000000001",
            "locale": "ru",
            "variables": {"order_id": "123"},
        }
        payload = NotificationPayload(**data)
        assert payload.event_type == "order.created"
        assert payload.variables["order_id"] == "123"


class TestHealthEndpoint:
    async def test_health_ok(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "notification-service"
        assert "checkers" in data


class TestNotificationsEndpoint:
    async def test_get_notifications_empty(
        self, async_client: AsyncClient, db_session: AsyncSession
    ) -> None:
        response = await async_client.get("/notifications?status=unread")
        assert response.status_code == 403
