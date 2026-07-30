
from uuid import UUID

from pydantic import BaseModel


class ImportCompletedPayload(BaseModel):
    task_id: UUID
    import_type: str
    products_created: int
    errors: list[dict] = []


class ImportFailedPayload(BaseModel):
    task_id: UUID
    error: str
