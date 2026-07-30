"""Re-exports the shared ORM base and mixins.

The definitions live in `src.core.orm` so the core package stays free of
service-specific imports and can be extracted as a dependency. Model modules
keep importing from here.
"""

from src.core.orm import (
    Base,
    CreatedAtMixin,
    SoftDeleteMixin,
    TimestampMixin,
    metadata_obj,
)

__all__ = [
    "Base",
    "CreatedAtMixin",
    "SoftDeleteMixin",
    "TimestampMixin",
    "metadata_obj",
]
