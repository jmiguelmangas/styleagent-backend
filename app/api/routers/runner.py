from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from app.api.deps import get_store
from app.core.models import RunnerJob, RunnerJobComplete, RunnerJobCreate, RunnerJobHeartbeat
from app.storage.fs_store import FSStore

router = APIRouter(prefix="/runner", tags=["runner"])


@router.get(
    "/jobs",
    response_model=list[RunnerJob],
    summary="List Runner Jobs",
    description="List runner jobs with optional status filtering and limit.",
)
def list_runner_jobs(
    status_filter: str = Query(
        "pending",
        alias="status",
        description="Filter by job status. Default value is `pending`.",
    ),
    limit: int = Query(1, ge=1, le=100, description="Maximum number of jobs to return."),
    store: FSStore = Depends(get_store),
) -> list[RunnerJob]:
    return store.list_runner_jobs(status=status_filter, limit=limit)


@router.get(
    "/jobs/{job_id}",
    response_model=RunnerJob,
    summary="Get Runner Job",
    description="Fetch a specific runner job by job identifier.",
)
def get_runner_job(
    job_id: str = Path(..., description="Runner job identifier."),
    store: FSStore = Depends(get_store),
) -> RunnerJob:
    job = store.get_runner_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="runner job not found")
    return job


@router.post(
    "/jobs",
    response_model=RunnerJob,
    status_code=status.HTTP_201_CREATED,
    summary="Create Runner Job",
    description="Create a new runner job (debug/admin helper endpoint).",
)
def create_runner_job(
    payload: RunnerJobCreate = Body(..., description="Runner job payload."),
    store: FSStore = Depends(get_store),
) -> RunnerJob:
    job = RunnerJob(job_type=payload.job_type, payload=payload.payload)
    return store.create_runner_job(job)


@router.post(
    "/jobs/{job_id}/claim",
    response_model=RunnerJob,
    summary="Claim Runner Job",
    description="Mark a pending runner job as picked up.",
)
def claim_runner_job(
    job_id: str = Path(..., description="Runner job identifier."),
    store: FSStore = Depends(get_store),
) -> RunnerJob:
    job = store.get_runner_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="runner job not found")
    updated = store.update_runner_job(job_id, status="picked_up")
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="runner job not found")
    return updated


@router.post(
    "/jobs/{job_id}/heartbeat",
    response_model=RunnerJob,
    summary="Heartbeat Runner Job",
    description="Update in-progress runner job status.",
)
def heartbeat_runner_job(
    payload: RunnerJobHeartbeat = Body(..., description="Heartbeat payload."),
    job_id: str = Path(..., description="Runner job identifier."),
    store: FSStore = Depends(get_store),
) -> RunnerJob:
    updated = store.update_runner_job(job_id, status=payload.status)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="runner job not found")
    return updated


@router.post(
    "/jobs/{job_id}/complete",
    response_model=RunnerJob,
    summary="Complete Runner Job",
    description="Finalize a runner job with succeeded/failed status, result, error, and logs.",
)
def complete_runner_job(
    payload: RunnerJobComplete = Body(..., description="Completion payload."),
    job_id: str = Path(..., description="Runner job identifier."),
    store: FSStore = Depends(get_store),
) -> RunnerJob:
    updated = store.update_runner_job(
        job_id,
        status=payload.status,
        result=payload.result,
        error=payload.error,
        logs=payload.logs,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="runner job not found")
    return updated

