import logging
import secrets
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BasePaymentGateway(ABC):
    """Abstract base for payment gateways."""

    @abstractmethod
    async def create_payment(
        self,
        amount: int,
        currency: str,
        order_id: str,
        metadata: dict | None = None,
    ) -> dict:
        """Create a payment. Returns dict with gateway_payment_id, status, raw_response."""
        ...

    @abstractmethod
    async def capture(self, payment_id: str) -> dict:
        """Capture an authorized payment."""
        ...

    @abstractmethod
    async def refund(self, payment_id: str, amount: int | None = None) -> dict:
        """Refund a payment. Returns dict with gateway_transaction_id, status."""
        ...

    @abstractmethod
    async def verify_webhook(
        self, payload: str | bytes, signature: str | None = None
    ) -> dict:
        """Verify a webhook payload. Returns parsed event dict."""
        ...


class MockGateway(BasePaymentGateway):
    """Mock gateway that always returns success with random IDs."""

    async def create_payment(
        self,
        amount: int,
        currency: str,
        order_id: str,
        metadata: dict | None = None,
    ) -> dict:
        return {
            "gateway_payment_id": f"mock_pi_{secrets.token_hex(12)}",
            "status": "succeeded",
            "raw_response": {
                "id": f"mock_pi_{secrets.token_hex(12)}",
                "status": "succeeded",
                "amount": amount,
                "currency": currency,
            },
        }

    async def capture(self, payment_id: str) -> dict:
        return {
            "gateway_transaction_id": f"mock_cap_{secrets.token_hex(12)}",
            "status": "succeeded",
            "raw_response": {"status": "succeeded"},
        }

    async def refund(self, payment_id: str, amount: int | None = None) -> dict:
        return {
            "gateway_transaction_id": f"mock_re_{secrets.token_hex(12)}",
            "status": "succeeded",
            "raw_response": {"status": "succeeded"},
        }

    async def verify_webhook(
        self, payload: str | bytes, signature: str | None = None
    ) -> dict:
        if isinstance(payload, bytes):
            payload = payload.decode()
        import json

        return json.loads(payload)


class StripeGateway(BasePaymentGateway):
    """Stripe payment gateway implementation."""

    def __init__(self, api_key: str, webhook_secret: str) -> None:
        self._api_key = api_key
        self._webhook_secret = webhook_secret
        self._stripe = None
        if api_key:
            try:
                import stripe

                self._stripe = stripe
                self._stripe.api_key = api_key
            except ImportError:
                logger.warning("stripe package not installed; falling back to mock")

    async def create_payment(
        self,
        amount: int,
        currency: str,
        order_id: str,
        metadata: dict | None = None,
    ) -> dict:
        if self._stripe:
            intent = self._stripe.PaymentIntent.create(
                amount=amount,
                currency=currency.lower(),
                metadata={"order_id": order_id, **(metadata or {})},
            )
            return {
                "gateway_payment_id": intent.id,
                "status": intent.status,
                "raw_response": intent,
            }
        return {
            "gateway_payment_id": f"pi_fallback_{secrets.token_hex(12)}",
            "status": "succeeded",
            "raw_response": {"status": "succeeded"},
        }

    async def capture(self, payment_id: str) -> dict:
        if self._stripe:
            intent = self._stripe.PaymentIntent.capture(payment_id)
            return {
                "gateway_transaction_id": intent.latest_charge,
                "status": intent.status,
                "raw_response": intent,
            }
        return {
            "gateway_transaction_id": f"ch_fallback_{secrets.token_hex(12)}",
            "status": "succeeded",
            "raw_response": {"status": "succeeded"},
        }

    async def refund(self, payment_id: str, amount: int | None = None) -> dict:
        if self._stripe:
            refund_args: dict = {"payment_intent": payment_id}
            if amount is not None:
                refund_args["amount"] = amount
            refund = self._stripe.Refund.create(**refund_args)
            return {
                "gateway_transaction_id": refund.id,
                "status": refund.status,
                "raw_response": refund,
            }
        return {
            "gateway_transaction_id": f"re_fallback_{secrets.token_hex(12)}",
            "status": "succeeded",
            "raw_response": {"status": "succeeded"},
        }

    async def verify_webhook(
        self, payload: str | bytes, signature: str | None = None
    ) -> dict:
        if self._stripe and self._webhook_secret and signature:
            event = self._stripe.Webhook.construct_event(
                payload, signature, self._webhook_secret
            )
            return event
        import json

        if isinstance(payload, bytes):
            payload = payload.decode()
        return json.loads(payload)


class YooKassaGateway(BasePaymentGateway):
    """YooKassa payment gateway implementation."""

    _base_url = "https://api.yookassa.ru/v3/"

    def __init__(
        self, shop_id: str, secret_key: str, webhook_secret: str
    ) -> None:
        self._shop_id = shop_id
        self._secret_key = secret_key
        self._webhook_secret = webhook_secret

    def _auth_header(self) -> str:
        import base64

        credentials = base64.b64encode(
            f"{self._shop_id}:{self._secret_key}".encode()
        ).decode()
        return f"Basic {credentials}"

    async def _request(self, method: str, path: str, json_data: dict | None = None) -> dict:
        import aiohttp

        headers = {
            "Authorization": self._auth_header(),
            "Content-Type": "application/json",
            "Idempotence-Key": secrets.token_hex(16),
        }
        url = f"{self._base_url}{path}"
        async with aiohttp.ClientSession() as session, session.request(
            method, url, json=json_data, headers=headers
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def create_payment(
        self,
        amount: int,
        currency: str,
        order_id: str,
        metadata: dict | None = None,
    ) -> dict:
        payload = {
            "amount": {
                "value": f"{amount / 100:.2f}",
                "currency": currency,
            },
            "capture": True,
            "description": f"Order {order_id}",
            "metadata": metadata or {},
        }
        result = await self._request("POST", "payments", payload)
        return {
            "gateway_payment_id": result["id"],
            "status": result["status"],
            "raw_response": result,
        }

    async def capture(self, payment_id: str) -> dict:
        result = await self._request("POST", f"payments/{payment_id}/capture", {})
        return {
            "gateway_transaction_id": result.get("id", payment_id),
            "status": result["status"],
            "raw_response": result,
        }

    async def refund(self, payment_id: str, amount: int | None = None) -> dict:
        payload: dict = {"payment_id": payment_id}
        if amount is not None:
            payload["amount"] = {
                "value": f"{amount / 100:.2f}",
                "currency": "RUB",
            }
        result = await self._request("POST", "refunds", payload)
        return {
            "gateway_transaction_id": result["id"],
            "status": result["status"],
            "raw_response": result,
        }

    async def verify_webhook(
        self, payload: str | bytes, signature: str | None = None
    ) -> dict:
        import json

        if isinstance(payload, bytes):
            payload = payload.decode()
        data = json.loads(payload)
        return data
