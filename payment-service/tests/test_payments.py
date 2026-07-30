"""Integration tests for payment endpoints."""

from __future__ import annotations

import uuid
from unittest import mock

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_payment_success(test_app: AsyncClient, auth_headers: dict):
    """Test successful payment creation."""
    with (
        mock.patch(
            "src.routers.payments.get_token_payload",
            return_value=mock.MagicMock(
                type="access",
                user_uuid=str(uuid.uuid4()),
                permissions={},
                jti="test",
            ),
        ),
        mock.patch("src.services.payment_service.check_idempotency", return_value=True),
    ):
        payload = {
            "order_id": str(uuid.uuid4()),
            "user_uuid": str(uuid.uuid4()),
            "amount": 10000,
            "currency": "RUB",
            "payment_method": "MOCK",
            "idempotency_key": f"test-{uuid.uuid4().hex[:12]}",
        }
        response = await test_app.post("/payments", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] == payload["order_id"]
        assert data["amount"] == 10000
        assert data["status"] in ("SUCCEEDED", "PROCESSING")
        assert "id" in data


@pytest.mark.anyio
async def test_create_payment_idempotency(test_app: AsyncClient, auth_headers: dict):
    """Test payment idempotency: duplicate request returns existing payment."""
    order_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    idemp_key = f"test-idemp-{uuid.uuid4().hex[:12]}"

    with (
        mock.patch(
            "src.routers.payments.get_token_payload",
            return_value=mock.MagicMock(
                type="access",
                user_uuid=user_id,
                permissions={},
                jti="test",
            ),
        ),
        mock.patch(
            "src.services.payment_service.check_idempotency", side_effect=[True, False]
        ),
        mock.patch(
            "src.repositories.payment_repo.PaymentRepo.get_by_idempotency_key"
        ) as mock_get,
    ):
        from src.models.payment import Payment

        existing = Payment(
            id=uuid.uuid4(),
            order_id=order_id,
            user_uuid=user_id,
            amount=10000,
            currency="RUB",
            status="SUCCEEDED",
            payment_method="MOCK",
            gateway="mock",
            gateway_payment_id="mock_pi_test",
            idempotency_key=idemp_key,
        )
        mock_get.return_value = existing

        payload = {
            "order_id": order_id,
            "user_uuid": user_id,
            "amount": 10000,
            "currency": "RUB",
            "payment_method": "MOCK",
            "idempotency_key": idemp_key,
        }
        resp1 = await test_app.post("/payments", json=payload, headers=auth_headers)
        resp2 = await test_app.post("/payments", json=payload, headers=auth_headers)
        assert resp2.status_code == 200


@pytest.mark.anyio
async def test_get_payment_by_uuid(test_app: AsyncClient, auth_headers: dict):
    """Test retrieving a payment by UUID."""
    payment_id = str(uuid.uuid4())

    mock_payment = mock.MagicMock()
    mock_payment.id = payment_id
    mock_payment.order_id = str(uuid.uuid4())
    mock_payment.user_uuid = str(uuid.uuid4())
    mock_payment.amount = 10000
    mock_payment.currency = "RUB"
    mock_payment.status = "SUCCEEDED"
    mock_payment.payment_method = "MOCK"
    mock_payment.gateway = "mock"
    mock_payment.gateway_payment_id = "mock_pi_test"
    mock_payment.idempotency_key = None
    mock_payment.transactions = []
    mock_payment.created_at = "2024-01-01T00:00:00Z"
    mock_payment.updated_at = "2024-01-01T00:00:00Z"

    with (
        mock.patch(
            "src.routers.payments.get_token_payload",
            return_value=mock.MagicMock(
                type="access",
                user_uuid=str(uuid.uuid4()),
                permissions={},
                jti="test",
            ),
        ),
        mock.patch(
            "src.repositories.payment_repo.PaymentRepo.get_by_uuid",
            return_value=mock_payment,
        ),
    ):
        response = await test_app.get(f"/payments/{payment_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == payment_id
        assert data["amount"] == 10000


@pytest.mark.anyio
async def test_get_payment_not_found(test_app: AsyncClient, auth_headers: dict):
    """Test 404 when payment not found."""
    with (
        mock.patch(
            "src.routers.payments.get_token_payload",
            return_value=mock.MagicMock(
                type="access",
                user_uuid=str(uuid.uuid4()),
                permissions={},
                jti="test",
            ),
        ),
        mock.patch(
            "src.repositories.payment_repo.PaymentRepo.get_by_uuid",
            return_value=None,
        ),
    ):
        response = await test_app.get(f"/payments/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404


@pytest.mark.anyio
async def test_refund_payment(test_app: AsyncClient, auth_headers: dict):
    """Test successful payment refund."""
    payment_id = str(uuid.uuid4())

    mock_payment = mock.MagicMock()
    mock_payment.id = payment_id
    mock_payment.order_id = str(uuid.uuid4())
    mock_payment.user_uuid = str(uuid.uuid4())
    mock_payment.amount = 10000
    mock_payment.currency = "RUB"
    mock_payment.status = "REFUNDED"
    mock_payment.payment_method = "MOCK"
    mock_payment.gateway = "mock"
    mock_payment.gateway_payment_id = "mock_pi_test"
    mock_payment.idempotency_key = None
    mock_payment.transactions = []
    mock_payment.created_at = "2024-01-01T00:00:00Z"
    mock_payment.updated_at = "2024-01-01T00:00:00Z"

    with (
        mock.patch(
            "src.routers.payments.get_token_payload",
            return_value=mock.MagicMock(
                type="access",
                user_uuid=str(uuid.uuid4()),
                permissions={},
                jti="test",
            ),
        ),
        mock.patch(
            "src.services.payment_service.PaymentService.refund",
            return_value=mock_payment,
        ),
    ):
        response = await test_app.post(
            f"/payments/{payment_id}/refund",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REFUNDED"


@pytest.mark.anyio
async def test_refund_not_succeeded(test_app: AsyncClient, auth_headers: dict):
    """Test refund conflict when payment is not in SUCCEEDED state."""
    payment_id = str(uuid.uuid4())

    with (
        mock.patch(
            "src.routers.payments.get_token_payload",
            return_value=mock.MagicMock(
                type="access",
                user_uuid=str(uuid.uuid4()),
                permissions={},
                jti="test",
            ),
        ),
        mock.patch(
            "src.services.payment_service.PaymentService.refund",
            side_effect=ValueError("Cannot refund payment with status PENDING"),
        ),
    ):
        response = await test_app.post(
            f"/payments/{payment_id}/refund",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 409


@pytest.mark.anyio
async def test_unauthorized_access(test_app: AsyncClient):
    """Test 403 when no auth token is provided."""
    response = await test_app.post("/payments", json={})
    assert response.status_code == 403
