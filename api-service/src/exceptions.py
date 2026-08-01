"""Domain exceptions — layered architecture inner layer.

These exceptions are raised by routers/facades and mapped to HTTP status
codes by exception handlers in main.py. Never import fastapi.HTTPException
outside main.py.
"""


class DomainError(Exception):
    """Base domain exception."""


class NotFoundError(DomainError):
    """Resource not found → 404."""


class ValidationError(DomainError):
    """Invalid input → 400."""


class UnauthorizedError(DomainError):
    """Authentication required → 401."""


class ForbiddenError(DomainError):
    """Insufficient permissions → 403."""


class ServiceUnavailableError(DomainError):
    """A required downstream service is unreachable → 503."""
