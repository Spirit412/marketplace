from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.enums.payment_status import PaymentMethod


class CreatePaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: UUID = Field(
        description="Order id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000110"],
    )
    user_id: UUID = Field(
        description="Paying user id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000010"],
    )
    amount: int = Field(description="Amount to charge, in kopecks.", examples=[398000])
    currency: str = Field(
        default="RUB", description="ISO 4217 currency code.", examples=["RUB"]
    )
    payment_method: PaymentMethod = Field(
        description="Payment gateway to use.", examples=["STRIPE"]
    )
    idempotency_key: str = Field(
        description="Client-generated key to safely retry payment creation.",
        examples=["a1b2c3d4-e5f6-4789-9012-3456789abcde"],
    )


class RefundRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: int | None = Field(
        default=None,
        description="Amount to refund, in kopecks; omit for a full refund.",
        examples=[398000],
    )
