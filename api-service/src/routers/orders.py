from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request

from src.depends import Inject
from src.schemes.response.order import OrderFullResponse
from src.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get(
    "/{order_id}/full",
    summary="Order + payment status in one call",
)
async def get_order_full(
    order_id: Annotated[
        str,
        Path(
            description="order-service order UUID.",
            examples=["019f0000-0000-0000-0000-000000000010"],
        ),
    ],
    request: Request,
    service: Annotated[OrderService, Depends(Inject(OrderService))],
) -> OrderFullResponse:
    authorization = request.headers.get("Authorization", "")
    return await service.get_order_full(order_id, authorization)
