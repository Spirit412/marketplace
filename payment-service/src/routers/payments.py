import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.core.database import get_async_session
from src.depends import Inject
from src.exceptions import NotFoundError
from src.schemes.request.payment import CreatePaymentRequest, RefundRequest
from src.schemes.response.payment import PaymentResponse
from src.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/",
    status_code=201,
    summary="Create payment",
)
async def create_payment(
    body: CreatePaymentRequest,
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[PaymentService, Depends(Inject(PaymentService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> PaymentResponse:
    """Create a new payment for an order."""
    payment = await service.create_payment(
        session=session,
        order_id=body.order_id,
        user_id=body.user_id,
        amount=body.amount,
        currency=body.currency,
        payment_method=body.payment_method,
        idempotency_key=body.idempotency_key,
    )
    return PaymentResponse.model_validate(payment)


@router.get(
    "/{payment_uuid}",
    summary="Get payment by ID",
)
async def get_payment(
    payment_uuid: uuid.UUID,
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[PaymentService, Depends(Inject(PaymentService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> PaymentResponse:
    """Get payment details by UUID."""
    payment = await service.get_payment(session=session, payment_uuid=payment_uuid)
    if payment is None:
        msg = f"Payment {payment_uuid} not found"
        raise NotFoundError(msg)
    return PaymentResponse.model_validate(payment)


@router.post(
    "/{payment_uuid}/refund",
    summary="Refund payment",
)
async def refund_payment(
    payment_uuid: uuid.UUID,
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[PaymentService, Depends(Inject(PaymentService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    body: RefundRequest | None = None,
) -> PaymentResponse:
    """Refund a payment partially or in full."""
    payment = await service.refund(
        session=session,
        payment_uuid=payment_uuid,
        amount=body.amount if body is not None else None,
    )
    return PaymentResponse.model_validate(payment)
