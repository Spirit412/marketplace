from enum import StrEnum

from src.patterns.state_machine import StateMachine


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    CANCELLED = "CANCELLED"


PAYMENT_VALID_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.PENDING: {
        PaymentStatus.PROCESSING,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.PROCESSING: {
        PaymentStatus.SUCCEEDED,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.SUCCEEDED: {PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED},
    PaymentStatus.PARTIALLY_REFUNDED: {
        PaymentStatus.REFUNDED,
        PaymentStatus.PARTIALLY_REFUNDED,
    },
    PaymentStatus.FAILED: set(),
    PaymentStatus.CANCELLED: set(),
    PaymentStatus.REFUNDED: set(),
}

PAYMENT_STATE_MACHINE: StateMachine[PaymentStatus] = StateMachine(
    PAYMENT_VALID_TRANSITIONS
)


class PaymentMethod(StrEnum):
    STRIPE = "STRIPE"
    YOOKASSA = "YOOKASSA"
    MOCK = "MOCK"


class TransactionType(StrEnum):
    CAPTURE = "CAPTURE"
    REFUND = "REFUND"
