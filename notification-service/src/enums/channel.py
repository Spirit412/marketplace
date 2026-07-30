from enum import StrEnum


class Channel(StrEnum):
    email = "email"
    sms = "sms"
    push = "push"
    websocket = "websocket"
