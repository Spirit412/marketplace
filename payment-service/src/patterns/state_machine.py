from typing import Generic, TypeVar

StateT = TypeVar("StateT")


class InvalidTransitionError(Exception):
    """Raised when a transition isn't allowed by the state machine's transition graph."""

    def __init__(self, current: object, target: object) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Cannot transition from {current!r} to {target!r}")


class StateMachine(Generic[StateT]):
    """Validates status transitions against a fixed graph of allowed edges.

    Not tied to any one entity — construct one per status enum (OrderStatus,
    PaymentStatus, ...) with its own transition graph, and reuse it wherever
    that status needs a transition checked instead of assigned directly.
    """

    def __init__(self, transitions: dict[StateT, set[StateT]]) -> None:
        self._transitions = transitions

    def can_transition(self, current: StateT, target: StateT) -> bool:
        return target in self._transitions.get(current, set())

    def assert_transition(self, current: StateT, target: StateT) -> None:
        if not self.can_transition(current, target):
            raise InvalidTransitionError(current, target)

    def allowed_from(self, current: StateT) -> set[StateT]:
        return self._transitions.get(current, set())

    def is_terminal(self, state: StateT) -> bool:
        return not self._transitions.get(state)
