"""Domain exceptions — layered architecture inner layer.

These exceptions are raised by services and mapped to HTTP status codes
by exception handlers in main.py. Services never import fastapi.HTTPException.
"""


class DomainError(Exception):
    """Base domain exception."""


class NotFoundError(DomainError):
    """Resource not found → 404."""


class ConflictError(DomainError):
    """Resource already exists / state conflict → 409."""


class ValidationError(DomainError):
    """Invalid input / business rule violation → 400.

    Optionally carries every accumulated violation (see core/event/), not
    just the first one — the exception handler in main.py serializes
    `errors` as a list when there is more than one.
    """

    def __init__(self, message: str = "", *, errors: list[str] | None = None) -> None:
        self.errors: list[str] = (
            errors if errors is not None else ([message] if message else [])
        )
        super().__init__(message or "; ".join(self.errors))


class UnauthorizedError(DomainError):
    """Authentication required → 401."""


class ForbiddenError(DomainError):
    """Insufficient permissions → 403."""


class ServiceUnavailableError(DomainError):
    """Downstream service unavailable → 503."""
