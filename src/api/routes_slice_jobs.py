"""Slice job routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models.schemas import SliceJobCreate, SliceJobResponse
from ..services.slice_service import slice_service
from ..services.storage_service import storage_service
from ..core.errors import ApiError


router = APIRouter(prefix="/slice-jobs", tags=["slice-jobs"])


@router.post("", response_model=SliceJobResponse, status_code=201)
async def create_slice_job(
    job: SliceJobCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new slice job.

    The job will be queued and processed asynchronously.
    Poll the job status endpoint to check progress.
    """
    return await slice_service.create_slice_job(db=db, job_data=job)


@router.get("/{job_id}", response_model=SliceJobResponse)
async def get_slice_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get slice job status and results."""
    return await slice_service.get_slice_job(db=db, job_id=job_id)


@router.get("/{job_id}/gcode")
async def download_gcode(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download G-code output."""
    job = await slice_service.get_slice_job(db=db, job_id=job_id)

    if job.status != "completed":
        raise ApiError(
            code="JOB_NOT_COMPLETED",
            message="Job is not completed yet.",
            http_status=400,
            details={"job_id": job_id, "status": job.status},
        )

    gcode_path = storage_service.get_file_path(job_id, "output.gcode")

    if not gcode_path.exists():
        raise ApiError(
            code="FILE_NOT_FOUND",
            message="G-code file not found.",
            http_status=404,
            details={"job_id": job_id},
        )

    return FileResponse(
        path=str(gcode_path),
        media_type="application/octet-stream",
        filename=f"{job_id}_output.gcode",
    )


@router.get("/{job_id}/project.3mf")
async def download_project_3mf(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download 3MF project file."""
    job = await slice_service.get_slice_job(db=db, job_id=job_id)

    if job.status != "completed":
        raise ApiError(
            code="JOB_NOT_COMPLETED",
            message="Job is not completed yet.",
            http_status=400,
            details={"job_id": job_id, "status": job.status},
        )

    project_path = storage_service.get_file_path(job_id, "project.3mf")

    if not project_path.exists():
        raise ApiError(
            code="FILE_NOT_FOUND",
            message="3MF project file not found.",
            http_status=404,
            details={"job_id": job_id},
        )

    return FileResponse(
        path=str(project_path),
        media_type="application/octet-stream",
        filename=f"{job_id}_project.3mf",
    )
