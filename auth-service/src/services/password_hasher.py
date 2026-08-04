import bcrypt


class PasswordHasher:
    """Hash and verify passwords using bcrypt.

    The ``scheme`` parameter is accepted for config compatibility
    but the implementation always uses bcrypt (the only scheme
    suitable for password storage).
    """

    def __init__(self, scheme: str = "bcrypt") -> None:
        _ = scheme  # retained for config compatibility; always bcrypt

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
