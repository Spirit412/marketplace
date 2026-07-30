from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    SELLER = "seller"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    SYSTEM = "system"
