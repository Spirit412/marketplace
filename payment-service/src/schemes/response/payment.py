from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.enums.payment_status import PaymentMethod, PaymentStatus


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    transaction_type: str
    amount: int
    gateway_transaction_id: str | None
    created_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    user_id: UUID
    amount: int
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    gateway: str
    gateway_payment_id: str | None
    idempotency_key: str | None
    transactions: list[TransactionResponse]
    created_at: datetime
    updated_at: datetime
