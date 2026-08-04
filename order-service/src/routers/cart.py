from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path

from src.core.auth import TokenPayload, get_token_payload
from src.depends import Inject
from src.schemes.request.cart import CartItemRequest
from src.schemes.response.cart import CartResponse
from src.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])

ProductIdPath = Annotated[
    UUID,
    Path(
        description="Product id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000050"],
    ),
]


@router.get(
    "/",
    summary="Get cart",
)
async def get_cart(
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> CartResponse:
    """Get current user's cart."""
    return await service.get_cart_response(token_payload.user_id)


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
    return await service.add_item_response(
        user_id=token_payload.user_id,
        product_id=str(body.product_id),
        quantity=body.quantity,
    )


@router.delete(
    "/{product_id}",
    status_code=204,
    response_model=None,
    summary="Remove item from cart",
)
async def remove_from_cart(
    product_id: ProductIdPath,
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[CartService, Depends(Inject(CartService))],
) -> None:
    """Remove an item from the cart."""
    await service.remove_item(
        user_id=token_payload.user_id,
        product_id=str(product_id),
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
