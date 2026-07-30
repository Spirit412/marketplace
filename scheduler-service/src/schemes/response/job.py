from datetime import datetime

from pydantic import BaseModel


class JobStatus(BaseModel):
    """Individual job metadata returned by GET /jobs."""

    id: str
    name: str
    schedule: str
    next_run: datetime | None = None
    last_run: datetime | None = None
    is_running: bool = False


class JobList(BaseModel):
    """Wrapper for list of jobs."""

    jobs: list[JobStatus]
    total: int


class TriggerResponse(BaseModel):
    """Response for POST /jobs/{id}/trigger."""

    job_id: str
    run_id: str
    status: str = "accepted"
