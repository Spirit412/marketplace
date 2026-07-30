import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.core.auth import (
    Permission,
    TokenPayload,
    require_permission,
)
from src.core.database import get_async_session
from src.depends import Inject
from src.schemes.request.report import GenerateReportRequest
from src.schemes.response.report import ReportListResponse, ReportResponse
from src.services.report_service import ReportService


router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", response_model=ReportResponse, status_code=202, summary="Generate report")
async def generate_report(
    request: GenerateReportRequest,
    service: Annotated[ReportService, Depends(Inject(ReportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[
        TokenPayload,
        Depends(require_permission(settings.APP_ID, Permission.WRITE)),
    ],
) -> ReportResponse:
    """Generate a new report asynchronously."""
    return await service.generate(
        session=session,
        request=request,
        user_uuid=uuid.UUID(token_payload.user_uuid),
    )


@router.get("/{report_id}", response_model=ReportResponse, summary="Get report by ID")
async def get_report(
    report_id: uuid.UUID,
    service: Annotated[ReportService, Depends(Inject(ReportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[
        TokenPayload,
        Depends(require_permission(settings.APP_ID, Permission.READ)),
    ],
) -> ReportResponse:
    """Get report details by ID."""
    return await service.get_report(
        session=session,
        report_id=report_id,
    )


@router.get("/{report_id}/download", summary="Download report")
async def download_report(
    report_id: uuid.UUID,
    service: Annotated[ReportService, Depends(Inject(ReportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[
        TokenPayload,
        Depends(require_permission(settings.APP_ID, Permission.READ)),
    ],
) -> StreamingResponse:
    """Download a generated report file."""
    content, filename, media_type = await service.download(
        session=session,
        report_id=report_id,
    )
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/", response_model=ReportListResponse, summary="List reports")
async def list_reports(
    service: Annotated[ReportService, Depends(Inject(ReportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[
        TokenPayload,
        Depends(require_permission(settings.APP_ID, Permission.READ)),
    ],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> ReportListResponse:
    """List reports for the authenticated user with pagination."""
    return await service.list_reports(
        session=session,
        user_uuid=uuid.UUID(token_payload.user_uuid),
        offset=offset,
        limit=limit,
    )
