from enum import StrEnum


class EventType(StrEnum):
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_CANCELLED = "order.cancelled"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"
    STOCK_DEPLETED = "stock.depleted"
    USER_BLOCKED = "user.blocked"
    USER_UNBLOCKED = "user.unblocked"
    CART_EXPIRED = "cart.expired"
    REPORT_GENERATED = "report.generated"
    IMPORT_COMPLETED = "import.completed"
    IMPORT_FAILED = "import.failed"
