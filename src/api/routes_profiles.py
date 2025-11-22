"""Profile management routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models.schemas import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileListResponse,
    ProfileDeleteResponse,
)
from ..services.profiles_service import profiles_service


router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(
    profile: ProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new slicing profile."""
    return await profiles_service.create_profile(db=db, profile_data=profile)


@router.get("", response_model=ProfileListResponse)
async def list_profiles(
    source: Optional[str] = Query(None, description="Filter by source: 'builtin' or 'user'"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List slicing profiles."""
    return await profiles_service.list_profiles(
        db=db,
        source=source,
        limit=limit,
        offset=offset,
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get profile details by ID."""
    return await profiles_service.get_profile(db=db, profile_id=profile_id)


@router.patch("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: str,
    profile: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a profile (partial update)."""
    return await profiles_service.update_profile(
        db=db,
        profile_id=profile_id,
        profile_data=profile,
    )


@router.delete("/{profile_id}", response_model=ProfileDeleteResponse)
async def delete_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a profile."""
    return await profiles_service.delete_profile(db=db, profile_id=profile_id)
