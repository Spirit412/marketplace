from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StripeWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: str = Field(description="Raw Stripe event payload (JSON string).")
    signature: str = Field(description="Stripe-Signature header value.")


class YooKassaWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str = Field(
        description="YooKassa event type.", examples=["payment.succeeded"]
    )
    object: dict[str, Any] = Field(description="YooKassa event object payload.")
