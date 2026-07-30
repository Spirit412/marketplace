from abc import ABC, abstractmethod
from pathlib import Path


class BaseFileStorage(ABC):
    @abstractmethod
    async def save(self, content: bytes, path: str) -> str: ...

    @abstractmethod
    async def get(self, path: str) -> bytes: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...

    @abstractmethod
    async def get_download_url(self, path: str, ttl: int = 3600) -> str: ...


class LocalFileStorage(BaseFileStorage):
    def __init__(self, base_dir: str = "/tmp/reports") -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, content: bytes, path: str) -> str:
        full_path = self._base_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return str(full_path)

    async def get(self, path: str) -> bytes:
        full_path = self._base_dir / path
        if not full_path.exists():
            raise FileNotFoundError(f"Report file not found: {path}")
        return full_path.read_bytes()

    async def delete(self, path: str) -> None:
        full_path = self._base_dir / path
        if full_path.exists():
            full_path.unlink()

    async def get_download_url(self, path: str, ttl: int = 3600) -> str:
        return f"/api/reports/download/{path}"


class S3FileStorage(BaseFileStorage):
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
    ) -> None:
        self._endpoint_url = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket

    async def save(self, content: bytes, path: str) -> str:
        return f"s3://{self._bucket}/{path}"

    async def get(self, path: str) -> bytes:
        raise NotImplementedError("S3 storage not yet implemented")

    async def delete(self, path: str) -> None:
        raise NotImplementedError("S3 storage not yet implemented")

    async def get_download_url(self, path: str, ttl: int = 3600) -> str:
        raise NotImplementedError("S3 storage not yet implemented")
