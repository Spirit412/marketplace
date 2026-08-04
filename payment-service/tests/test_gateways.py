"""Unit tests for payment gateways."""

from __future__ import annotations

from src.config.settings import get_settings
from src.enums.payment_status import PaymentMethod
from src.services.gateway_registry import PaymentGatewayRegistry
from src.services.gateway_strategy import (
    MockGateway,
    StripeGateway,
    YooKassaGateway,
)


class TestMockGateway:
    """Tests for the Mock payment gateway."""

    async def test_mock_gateway_create_payment(self):
        gateway = MockGateway()
        result = await gateway.create_payment(
            amount=10000,
            currency="RUB",
            order_id="test-order-id",
        )
        assert "gateway_payment_id" in result
        assert result["gateway_payment_id"].startswith("mock_pi_")
        assert result["status"] == "succeeded"
        assert "raw_response" in result

    async def test_mock_gateway_refund(self):
        gateway = MockGateway()
        result = await gateway.refund("mock_pi_test")
        assert "gateway_transaction_id" in result
        assert result["gateway_transaction_id"].startswith("mock_re_")
        assert result["status"] == "succeeded"

    async def test_mock_gateway_capture(self):
        gateway = MockGateway()
        result = await gateway.capture("mock_pi_test")
        assert "gateway_transaction_id" in result
        assert result["gateway_transaction_id"].startswith("mock_cap_")
        assert result["status"] == "succeeded"

    async def test_mock_gateway_verify_webhook(self):
        gateway = MockGateway()
        payload = '{"type": "payment.succeeded", "object": {"id": "test"}}'
        result = await gateway.verify_webhook(payload)
        assert result["type"] == "payment.succeeded"


class TestGatewayRegistry:
    """Tests for the PaymentGatewayRegistry."""

    def test_gateway_registry_returns_mock(self):
        settings = get_settings()
        registry = PaymentGatewayRegistry(settings)
        gateway = registry.get_gateway(PaymentMethod.MOCK)
        assert isinstance(gateway, MockGateway)

    def test_gateway_registry_caches_instances(self):
        settings = get_settings()
        registry = PaymentGatewayRegistry(settings)
        gw1 = registry.get_gateway(PaymentMethod.MOCK)
        gw2 = registry.get_gateway(PaymentMethod.MOCK)
        assert gw1 is gw2

    def test_gateway_registry_returns_stripe(self):
        settings = get_settings()
        stripe_settings = type(settings)(
            **{
                **settings.model_dump(),
                "STRIPE_API_KEY": "sk_test_fake",
                "STRIPE_WEBHOOK_SECRET": "whsec_fake",
            }
        )
        registry = PaymentGatewayRegistry(stripe_settings)
        gateway = registry.get_gateway(PaymentMethod.STRIPE)
        assert isinstance(gateway, StripeGateway)

    def test_gateway_registry_returns_yookassa(self):
        settings = get_settings()
        yk_settings = type(settings)(
            **{
                **settings.model_dump(),
                "YOOKASSA_SHOP_ID": "test_shop",
                "YOOKASSA_SECRET_KEY": "test_key",
                "YOOKASSA_WEBHOOK_SECRET": "test_whsec",
            }
        )
        registry = PaymentGatewayRegistry(yk_settings)
        gateway = registry.get_gateway(PaymentMethod.YOOKASSA)
        assert isinstance(gateway, YooKassaGateway)
