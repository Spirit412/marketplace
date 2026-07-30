from src.models.payment import Payment, Transaction


class PaymentPayloadBuilder:
    """Builds payloads for payment events."""

    @staticmethod
    def build_succeeded(payment: Payment) -> dict:
        return {
            "payment_id": str(payment.id),
            "order_id": str(payment.order_id),
            "gateway_payment_id": payment.gateway_payment_id,
            "amount": payment.amount,
            "currency": payment.currency,
        }

    @staticmethod
    def build_failed(payment: Payment, reason: str) -> dict:
        return {
            "payment_id": str(payment.id),
            "order_id": str(payment.order_id),
            "reason": reason,
            "amount": payment.amount,
            "currency": payment.currency,
        }

    @staticmethod
    def build_refunded(payment: Payment, transaction: Transaction) -> dict:
        return {
            "payment_id": str(payment.id),
            "order_id": str(payment.order_id),
            "amount": transaction.amount,
            "gateway_transaction_id": transaction.gateway_transaction_id,
        }
