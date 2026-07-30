import uuid

from pydantic import BaseModel


class PaymentSucceededPayload(BaseModel):
    payment_id: uuid.UUID
    order_id: uuid.UUID
    gateway_payment_id: str
    amount: int
    currency: str


class PaymentFailedPayload(BaseModel):
    payment_id: uuid.UUID
    order_id: uuid.UUID
    reason: str


class PaymentRefundedPayload(BaseModel):
    payment_id: uuid.UUID
    order_id: uuid.UUID
    amount: int
    gateway_transaction_id: str
