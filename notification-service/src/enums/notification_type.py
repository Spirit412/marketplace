from enum import StrEnum


class NotificationType(StrEnum):
    error = "error"
    warning = "warning"
    info = "info"
    success = "success"
