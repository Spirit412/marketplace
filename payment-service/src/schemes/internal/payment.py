from uuid import UUID

from pydantic import BaseModel


class PaymentSucceededPayload(BaseModel):
    payment_id: UUID
    order_id: UUID
    gateway_payment_id: str
    amount: int
    currency: str


class PaymentFailedPayload(BaseModel):
    payment_id: UUID
    order_id: UUID
    reason: str


class PaymentRefundedPayload(BaseModel):
    payment_id: UUID
    order_id: UUID
    amount: int
    gateway_transaction_id: str
