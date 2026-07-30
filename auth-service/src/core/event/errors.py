class EventError(Exception):
    """Raised by a validator to report one failed business rule.

    Unlike a plain exception used for fail-fast control flow, EventError is
    designed to be *caught and collected* by EventManager rather than
    propagated — see manager.py. This lets a caller see every violated rule
    in one response instead of fixing them one HTTP round-trip at a time.
    """

    def __init__(self, detail: str, *, code: str | None = None) -> None:
        self.detail = detail
        self.code = code
        super().__init__(detail)
