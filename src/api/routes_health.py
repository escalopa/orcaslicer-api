"""Health check routes."""

import subprocess
import time
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models.db_models import Profile
from ..models.schemas import HealthResponse
from ..core.config import settings


router = APIRouter(tags=["health"])

start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.

    Returns service status, OrcaSlicer availability, and other metrics.
    """
    # Check OrcaSlicer CLI
    orca_available = Path(settings.orca_cli_path).exists()
    orca_version = None

    if orca_available:
        try:
            # Try to get version
            result = subprocess.run(
                [settings.orca_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                orca_version = result.stdout.strip()
        except Exception:
            pass

    # Count profiles
    count_result = await db.execute(select(func.count(Profile.id)))
    profiles_count = count_result.scalar_one()

    # Calculate uptime
    uptime_seconds = int(time.time() - start_time)

    return HealthResponse(
        status="ok",
        orca_cli_available=orca_available,
        orca_version=orca_version,
        profiles_loaded=profiles_count,
        uptime_seconds=uptime_seconds,
    )
