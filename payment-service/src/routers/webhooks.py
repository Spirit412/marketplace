import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.depends import Inject
from src.schemes.request.webhook import StripeWebhookRequest, YooKassaWebhookRequest
from src.services.payment_service import PaymentService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", status_code=200, summary="Handle Stripe webhook")
async def stripe_webhook(
    body: StripeWebhookRequest,
    service: Annotated[PaymentService, Depends(Inject(PaymentService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, Any]:
    """Handle incoming Stripe webhook event."""
    await service.handle_stripe_webhook(
        session=session,
        payload=body.payload,
        signature=body.signature,
    )
    return {"status": "ok"}


@router.post("/yookassa", status_code=200, summary="Handle YooKassa webhook")
async def yookassa_webhook(
    body: YooKassaWebhookRequest,
    service: Annotated[PaymentService, Depends(Inject(PaymentService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, Any]:
    """Handle incoming YooKassa webhook event."""
    full_payload = json.dumps({"event": body.event, "object": body.object})
    await service.handle_yookassa_webhook(
        session=session,
        payload=full_payload,
    )
    return {"status": "ok"}
