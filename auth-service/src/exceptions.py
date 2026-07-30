
class DomainError(Exception):
    """Base domain exception."""


class NotFoundError(DomainError):
    """Resource not found → 404."""


class ConflictError(DomainError):
    """Resource already exists / state conflict → 409."""


class ValidationError(DomainError):
    """Invalid input / business rule violation → 400."""


class UnauthorizedError(DomainError):
    """Authentication required → 401."""


class ForbiddenError(DomainError):
    """Insufficient permissions → 403."""


class ServiceUnavailableError(DomainError):
    """Downstream service unavailable → 503."""
