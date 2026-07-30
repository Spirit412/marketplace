
from pydantic import BaseModel, ConfigDict


class StripeWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload: str
    signature: str


class YooKassaWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: str
    object: dict
