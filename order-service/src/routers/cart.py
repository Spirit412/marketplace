from src.config.settings import settings
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.auth import Permission, TokenPayload, get_token_payload, require_permission
from src.depends import Inject
from src.schemes.request.cart import CartItemRequest
from src.schemes.response.cart import CartItemResponse, CartResponse
from src.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartResponse, summary="Get cart",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_cart(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> CartResponse:
    """Get current user's cart."""
    items = await service.get_cart(token_payload.user_uuid)
    cart_items = [
        CartItemResponse(product_id=uuid.UUID(k), quantity=v)
        for k, v in items.items()
    ]
    return CartResponse(items=cart_items)


@router.post("/", response_model=CartResponse, summary="Add item to cart",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def add_to_cart(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    body: CartItemRequest,
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> CartResponse:
    """Add an item to the cart."""
    items = await service.add_item(
        user_uuid=token_payload.user_uuid,
        product_uuid=str(body.product_id),
        quantity=body.quantity,
    )
    cart_items = [
        CartItemResponse(product_id=uuid.UUID(k), quantity=v)
        for k, v in items.items()
    ]
    return CartResponse(items=cart_items)


@router.delete("/{product_uuid}", status_code=204, response_model=None, summary="Remove item from cart",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.ALL))],
)
async def remove_from_cart(
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> None:
    """Remove an item from the cart."""
    await service.remove_item(
        user_uuid=token_payload.user_uuid,
        product_uuid=str(product_uuid),
    )


@router.delete("/", status_code=204, response_model=None, summary="Clear cart",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.ALL))],
)
async def clear_cart(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> None:
    """Clear the entire cart."""
    await service.clear_cart(token_payload.user_uuid)
