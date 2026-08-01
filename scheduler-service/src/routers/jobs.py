from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.core.datatype import uuid7
from src.dependencies import get_scheduler
from src.schemes.response.job import JobList, JobStatus, TriggerResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get(
    "/",
    summary="List scheduled jobs",
)
async def list_jobs(
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
    scheduler: Annotated[Any, Depends(get_scheduler)],
) -> JobList:
    """List all registered jobs with their status."""
    jobs = [
        JobStatus(
            id=job.id,
            name=job.name,
            schedule=str(job.trigger) if job.trigger else "manual",
            next_run=job.next_run_time,
            last_run=None,
            is_running=job.next_run_time is not None,
        )
        for job in scheduler.get_jobs()
    ]
    return JobList(jobs=jobs, total=len(jobs))


@router.post(
    "/{job_id}/trigger",
    status_code=202,
    summary="Trigger job",
)
async def trigger_job(
    job_id: str,
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
    scheduler: Annotated[Any, Depends(get_scheduler)],
) -> TriggerResponse:
    """Trigger a job manually outside its schedule."""
    job = scheduler.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    try:
        run_id = str(uuid7())
        await job.func()
        return TriggerResponse(job_id=job_id, run_id=run_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
