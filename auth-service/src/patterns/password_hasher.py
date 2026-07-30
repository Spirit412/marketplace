import hashlib


class PasswordHasher:
    def __init__(self, scheme: str = "sha256") -> None:
        self._scheme = scheme

    def hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify(self, password: str, password_hash: str) -> bool:
        return self.hash(password) == password_hash
