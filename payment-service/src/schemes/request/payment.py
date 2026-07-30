import uuid

from pydantic import BaseModel, ConfigDict

from src.enums.payment_status import PaymentMethod


class CreatePaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: uuid.UUID
    user_uuid: uuid.UUID
    amount: int
    currency: str = "RUB"
    payment_method: PaymentMethod
    idempotency_key: str


class RefundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int | None = None
