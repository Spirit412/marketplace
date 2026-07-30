from src.config.settings import settings
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.core.auth import Permission, TokenPayload, get_token_payload, require_permission
from src.dependencies import get_scheduler
from src.schemes.response.job import JobList, JobStatus, TriggerResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=JobList, summary="List scheduled jobs",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.READ))],
)
async def list_jobs(
    token: TokenPayload = Depends(get_token_payload),
    scheduler: Any = Depends(get_scheduler),
) -> JobList:
    """List all registered jobs with their status."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            JobStatus(
                id=job.id,
                name=job.name,
                schedule=str(job.trigger) if job.trigger else "manual",
                next_run=job.next_run_time,
                last_run=None,
                is_running=job.next_run_time is not None,
            )
        )
    return JobList(jobs=jobs, total=len(jobs))


@router.post("/{job_id}/trigger", response_model=TriggerResponse, status_code=202, summary="Trigger job",
    dependencies=[Depends(require_permission(settings.APP_ID, Permission.WRITE))],
)
async def trigger_job(
    job_id: str,
    token: TokenPayload = Depends(get_token_payload),
    scheduler: Any = Depends(get_scheduler),
) -> TriggerResponse:
    """Trigger a job manually outside its schedule."""
    job = scheduler.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    try:
        run_id = str(uuid.uuid4())
        await job.func()
        return TriggerResponse(job_id=job_id, run_id=run_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
