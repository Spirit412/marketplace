from enum import StrEnum


class MovementType(StrEnum):
    RECEIPT = "receipt"
    SHIPMENT = "shipment"
    RESERVE = "reserve"
    RELEASE = "release"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
