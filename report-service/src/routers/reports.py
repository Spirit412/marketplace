from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.core.database import get_async_session
from src.depends import Inject
from src.schemes.request.report import GenerateReportRequest
from src.schemes.response.report import ReportListResponse, ReportResponse
from src.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])

ReportIdPath = Annotated[
    UUID,
    Path(
        description="Report id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000130"],
    ),
]


@router.post("/", status_code=202, summary="Generate report")
async def generate_report(
    request: GenerateReportRequest,
    service: Annotated[ReportService, Depends(Inject(ReportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> ReportResponse:
    """Generate a new report asynchronously."""
    return await service.generate(
        session=session,
        request=request,
        user_id=UUID(token_payload.user_id),
    )


@router.get("/{report_id}", summary="Get report by ID")
async def get_report(
    report_id: ReportIdPath,
    service: Annotated[ReportService, Depends(Inject(ReportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
) -> ReportResponse:
    """Get report details by ID."""
    return await service.get_report(
        session=session,
        report_id=report_id,
    )


@router.get("/{report_id}/download", summary="Download report")
async def download_report(
    report_id: ReportIdPath,
    service: Annotated[ReportService, Depends(Inject(ReportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    _token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
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


@router.get("/", summary="List reports")
async def list_reports(
    service: Annotated[ReportService, Depends(Inject(ReportService))],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    token_payload: Annotated[TokenPayload, Depends(get_token_payload)],
    offset: Annotated[int, Query(ge=0, description="Rows to skip.")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max rows to return.")] = 50,
) -> ReportListResponse:
    """List reports for the authenticated user with pagination."""
    return await service.list_reports(
        session=session,
        user_id=UUID(token_payload.user_id),
        offset=offset,
        limit=limit,
    )
