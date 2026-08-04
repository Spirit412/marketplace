from enum import StrEnum

from src.core.state_machine import StateMachine


class OrderStatus(StrEnum):
    """Order lifecycle states."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}

ORDER_STATE_MACHINE: StateMachine[OrderStatus] = StateMachine(VALID_TRANSITIONS)


class PaymentMethod(StrEnum):
    """Supported payment gateways."""

    STRIPE = "STRIPE"
    YOOKASSA = "YOOKASSA"
    MOCK = "MOCK"


class TaxStrategy(StrEnum):
    """Tax calculation regions."""

    RU = "RU"
    US = "US"
    EU = "EU"
