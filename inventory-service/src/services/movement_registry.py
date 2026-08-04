from collections.abc import Callable
from typing import Any

from src.enums.movement_type import MovementType

HandlerFunc = Callable[..., Any]

MOVEMENT_TYPE_HANDLERS: dict[MovementType, HandlerFunc] = {}


def register_handler(
    movement_type: MovementType,
) -> Callable[[HandlerFunc], HandlerFunc]:
    """Decorator to register a handler for a movement type."""

    def decorator(func: HandlerFunc) -> HandlerFunc:
        MOVEMENT_TYPE_HANDLERS[movement_type] = func
        return func

    return decorator
