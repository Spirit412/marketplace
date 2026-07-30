from enum import StrEnum

from src.patterns.state_machine import StateMachine


class ImportStatus(StrEnum):
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


IMPORT_VALID_TRANSITIONS: dict[ImportStatus, set[ImportStatus]] = {
    ImportStatus.PENDING: {ImportStatus.VALIDATING},
    ImportStatus.VALIDATING: {ImportStatus.PROCESSING, ImportStatus.FAILED},
    ImportStatus.PROCESSING: {ImportStatus.COMPLETED, ImportStatus.FAILED},
    ImportStatus.COMPLETED: set(),
    ImportStatus.FAILED: set(),
}

IMPORT_STATE_MACHINE: StateMachine[ImportStatus] = StateMachine(IMPORT_VALID_TRANSITIONS)
