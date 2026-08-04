from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Path, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.core.database import get_async_session
from src.dependencies import Inject
from src.exceptions import NotFoundError
from src.schemes.response.import_dto import ImportErrorResponse, ImportTaskResponse
from src.services.import_service import ImportService

router = APIRouter(prefix="/imports", tags=["imports"])

TaskIdPath = Annotated[
    UUID,
    Path(
        description="Import task id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000070"],
    ),
]


@router.post(
    "/upload",
    status_code=201,
    summary="Upload CSV file for import",
)
async def upload_csv(
    file: Annotated[UploadFile, File(description="CSV file to import.")],
    import_type: Annotated[
        str,
        Form(
            description="Kind of data being imported.",
            examples=["products"],
        ),
    ],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[ImportService, Depends(Inject(ImportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ImportTaskResponse:
    """Upload a CSV file for processing as an import task."""
    content = await file.read()
    seller_id = UUID(token_payload.user_id)

    task = await service.create_task(
        session=session,
        seller_id=seller_id,
        import_type=import_type,
        file_name=file.filename,
        content=content,
    )

    return ImportTaskResponse.model_validate(task)


@router.get(
    "/{task_id}",
    summary="Get import task by ID",
)
async def get_import_task(
    task_id: TaskIdPath,
    service: Annotated[ImportService, Depends(Inject(ImportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ImportTaskResponse:
    """Get import task status by task ID."""
    task = await service.get_task_status(session=session, task_id=task_id)
    if task is None:
        raise NotFoundError("Import task not found")
    return ImportTaskResponse.model_validate(task)


@router.get(
    "/{task_id}/errors",
    summary="Get import task errors",
)
async def get_task_errors(
    task_id: TaskIdPath,
    service: Annotated[ImportService, Depends(Inject(ImportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    offset: Annotated[int, Query(ge=0, description="Rows to skip.")] = 0,
    limit: Annotated[int, Query(ge=1, le=500, description="Max rows to return.")] = 100,
) -> ImportErrorResponse:
    """Get errors for a specific import task with pagination."""
    return await service.get_task_errors_response(
        session=session,
        task_id=task_id,
        offset=offset,
        limit=limit,
    )
