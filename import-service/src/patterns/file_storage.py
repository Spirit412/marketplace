from abc import ABC, abstractmethod
from hashlib import sha256
from pathlib import Path

from src.config.settings import settings


class BaseFileStorage(ABC):
    @abstractmethod
    async def save(self, file_content: bytes, key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def read(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> bool:
        raise NotImplementedError


class LocalFileStorage(BaseFileStorage):
    def __init__(self) -> None:
        self._base_dir = Path(settings.STORAGE_DIR)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _hash_key(self, key: str) -> str:
        return sha256(key.encode()).hexdigest()[:32]

    async def save(self, file_content: bytes, key: str) -> str:
        hashed = self._hash_key(key)
        file_path = self._base_dir / hashed
        file_path.write_bytes(file_content)
        return str(file_path)

    async def read(self, key: str) -> bytes:
        hashed = self._hash_key(key)
        file_path = self._base_dir / hashed
        return file_path.read_bytes()

    async def delete(self, key: str) -> bool:
        hashed = self._hash_key(key)
        file_path = self._base_dir / hashed
        if file_path.exists():
            file_path.unlink()
            return True
        return False


class S3FileStorage(BaseFileStorage):
    async def save(self, file_content: bytes, key: str) -> str:
        raise NotImplementedError("S3 storage is not yet implemented")

    async def read(self, key: str) -> bytes:
        raise NotImplementedError("S3 storage is not yet implemented")

    async def delete(self, key: str) -> bool:
        raise NotImplementedError("S3 storage is not yet implemented")
