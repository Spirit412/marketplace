from src.core.event.errors import EventError
from src.core.event.validator import BaseEventValidator, ContextT


class EventManager:
    """Runs a chain of validators against a context, accumulating every failure.

    Ported from the web_milk_back event-validation pattern: validators do not
    short-circuit each other. All of them run; every EventError raised is
    collected and returned together, so a caller can report every violated
    rule to the user at once ("product #1 not found, product #3 out of
    stock") instead of one raise-fast error per request round-trip.
    """

    @staticmethod
    async def validate_all(
        validators: list[BaseEventValidator[ContextT]],
        context: ContextT,
    ) -> list[EventError]:
        errors: list[EventError] = []
        for validator in validators:
            try:
                await validator.validate(context)
            except EventError as exc:
                errors.append(exc)
        return errors
