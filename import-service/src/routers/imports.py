from src.config.settings import settings
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import Permission, TokenPayload, get_token_payload, require_permission
from src.core.database import get_async_session
from src.dependencies import Inject
from src.exceptions import NotFoundError, ValidationError
from src.schemes.response.import_dto import ImportErrorResponse, ImportTaskResponse
from src.services.import_service import ImportService

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/upload", response_model=ImportTaskResponse, status_code=201, summary="Upload CSV file for import",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def upload_csv(
    file: Annotated[UploadFile, File()],
    import_type: Annotated[str, Form()],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[ImportService, Depends(Inject(ImportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ImportTaskResponse:
    """Upload a CSV file for processing as an import task."""
    if not file.filename:
        raise ValidationError("No file provided")

    content = await file.read()
    seller_id = uuid.UUID(token_payload.user_uuid)

    task = await service.create_task(
        session=session,
        seller_id=seller_id,
        import_type=import_type,
        file_name=file.filename,
        content=content,
    )

    return ImportTaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=ImportTaskResponse, summary="Get import task by ID",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_import_task(
    task_id: uuid.UUID,
    service: Annotated[ImportService, Depends(Inject(ImportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ImportTaskResponse:
    """Get import task status by task ID."""
    task = await service.get_task_status(session=session, task_id=task_id)
    if task is None:
        raise NotFoundError("Import task not found")
    return ImportTaskResponse.model_validate(task)


@router.get("/{task_id}/errors", response_model=ImportErrorResponse, summary="Get import task errors",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def get_task_errors(
    task_id: uuid.UUID,
    service: Annotated[ImportService, Depends(Inject(ImportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    offset: int = 0,
    limit: int = 100,
) -> ImportErrorResponse:
    """Get errors for a specific import task with pagination."""
    errors = await service.get_task_errors(
        session=session,
        task_id=task_id,
        offset=offset,
        limit=limit,
    )
    rows = [
        {
            "row_number": row.row_number,
            "errors": row.error_description or {},
        }
        for row in errors
    ]
    return ImportErrorResponse(rows=rows)
