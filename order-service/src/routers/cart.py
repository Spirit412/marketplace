import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from src.core.auth import TokenPayload, get_token_payload
from src.depends import Inject
from src.schemes.request.cart import CartItemRequest
from src.schemes.response.cart import CartItemResponse, CartResponse
from src.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get(
    "/",
    summary="Get cart",
)
async def get_cart(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> CartResponse:
    """Get current user's cart."""
    items = await service.get_cart(token_payload.user_id)
    cart_items = [
        CartItemResponse(product_id=uuid.UUID(k), quantity=v) for k, v in items.items()
    ]
    return CartResponse(items=cart_items)


@router.post(
    "/",
    summary="Add item to cart",
)
async def add_to_cart(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    body: CartItemRequest,
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> CartResponse:
    """Add an item to the cart."""
    items = await service.add_item(
        user_id=token_payload.user_id,
        product_uuid=str(body.product_id),
        quantity=body.quantity,
    )
    cart_items = [
        CartItemResponse(product_id=uuid.UUID(k), quantity=v) for k, v in items.items()
    ]
    return CartResponse(items=cart_items)


@router.delete(
    "/{product_uuid}",
    status_code=204,
    response_model=None,
    summary="Remove item from cart",
)
async def remove_from_cart(
    product_uuid: uuid.UUID,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> None:
    """Remove an item from the cart."""
    await service.remove_item(
        user_id=token_payload.user_id,
        product_uuid=str(product_uuid),
    )


@router.delete(
    "/",
    status_code=204,
    response_model=None,
    summary="Clear cart",
)
async def clear_cart(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> None:
    """Clear the entire cart."""
    await service.clear_cart(token_payload.user_id)
