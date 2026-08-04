from typing import Annotated

from fastapi import APIRouter, Depends, Path

from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.dependencies import get_scheduler_job_service
from src.schemes.response.job import JobList, TriggerResponse
from src.services.scheduler_job_service import SchedulerJobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get(
    "/",
    summary="List scheduled jobs",
)
async def list_jobs(
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[SchedulerJobService, Depends(get_scheduler_job_service)],
) -> JobList:
    """List all registered jobs with their status."""
    return service.list_jobs()


@router.post(
    "/{job_id}/trigger",
    status_code=202,
    summary="Trigger job",
)
async def trigger_job(
    job_id: Annotated[
        str,
        Path(
            description="Registered job id.",
            examples=["cancel_unpaid_orders"],
        ),
    ],
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[SchedulerJobService, Depends(get_scheduler_job_service)],
) -> TriggerResponse:
    """Trigger a job manually outside its schedule."""
    return await service.trigger(job_id)
