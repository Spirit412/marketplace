from src.config.settings import settings
from src.services.file_storage import BaseFileStorage, LocalFileStorage, S3FileStorage


class FileStorageRegistry:
    def __init__(self) -> None:
        self._backends: dict[str, BaseFileStorage] = {
            "local": LocalFileStorage(),
            "s3": S3FileStorage(),
        }
        backend_name = settings.STORAGE_BACKEND
        self._backend = self._backends.get(backend_name, self._backends["local"])

    @property
    def backend(self) -> BaseFileStorage:
        return self._backend
