from abc import ABC, abstractmethod
from typing import Generic, TypeVar

ContextT = TypeVar("ContextT")


class BaseEventValidator(ABC, Generic[ContextT]):
    """One business rule. Raises EventError on violation, returns None otherwise.

    Concrete validators receive whatever context object the call site needs
    (a dict, a dataclass, an ORM-bound draft entity) — EventManager does not
    care about its shape, only that validators raise EventError instead of
    an arbitrary exception.
    """

    @abstractmethod
    async def validate(self, context: ContextT) -> None: ...
