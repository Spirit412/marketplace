from src.config.settings import Settings
from src.enums.payment_status import PaymentMethod
from src.services.gateway_strategy import (
    BasePaymentGateway,
    MockGateway,
    StripeGateway,
    YooKassaGateway,
)


class PaymentGatewayRegistry:
    """Registry that returns the appropriate gateway for a given payment method."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._gateways: dict[PaymentMethod, BasePaymentGateway] = {}

    def get_gateway(self, payment_method: PaymentMethod) -> BasePaymentGateway:
        if payment_method not in self._gateways:
            self._gateways[payment_method] = self._build_gateway(payment_method)
        return self._gateways[payment_method]

    def _build_gateway(self, payment_method: PaymentMethod) -> BasePaymentGateway:
        if payment_method == PaymentMethod.MOCK:
            return MockGateway()
        if payment_method == PaymentMethod.STRIPE:
            return StripeGateway(
                self._settings.STRIPE_API_KEY,
                self._settings.STRIPE_WEBHOOK_SECRET,
            )
        if payment_method == PaymentMethod.YOOKASSA:
            return YooKassaGateway(
                self._settings.YOOKASSA_SHOP_ID,
                self._settings.YOOKASSA_SECRET_KEY,
                self._settings.YOOKASSA_WEBHOOK_SECRET,
            )
        raise ValueError(f"Unknown payment method: {payment_method}")
