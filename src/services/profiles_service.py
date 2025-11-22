"""Profile management service."""

import secrets
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.db_models import Profile
from ..models.schemas import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileListResponse,
    ProfileDeleteResponse,
)
from ..core.errors import ProfileNotFoundError


class ProfilesService:
    """Service for managing slicing profiles."""

    @staticmethod
    def _generate_profile_id(name: str) -> str:
        """Generate profile ID from name."""
        # Create a slug-like ID from name
        slug = name.lower().replace(" ", "_").replace("@", "")
        slug = "".join(c for c in slug if c.isalnum() or c == "_")
        return f"prof_{slug}_{secrets.token_hex(2)}"

    @staticmethod
    def _profile_to_response(profile: Profile) -> ProfileResponse:
        """Convert Profile model to response."""
        return ProfileResponse(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            source=profile.source,
            vendor=profile.vendor,
            machine_id=profile.machine_id,
            process_id=profile.process_id,
            filament_id=profile.filament_id,
            settings_overrides=profile.settings_overrides,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    async def create_profile(
        self,
        db: AsyncSession,
        profile_data: ProfileCreate,
    ) -> ProfileResponse:
        """Create a new profile."""
        profile_id = self._generate_profile_id(profile_data.name)

        profile = Profile(
            id=profile_id,
            name=profile_data.name,
            description=profile_data.description,
            source=profile_data.source,
            vendor=profile_data.vendor,
            machine_id=profile_data.machine_id,
            process_id=profile_data.process_id,
            filament_id=profile_data.filament_id,
            settings_overrides=profile_data.settings_overrides,
        )

        db.add(profile)
        await db.commit()
        await db.refresh(profile)

        return self._profile_to_response(profile)

    async def get_profile(
        self,
        db: AsyncSession,
        profile_id: str,
    ) -> ProfileResponse:
        """Get profile by ID."""
        result = await db.execute(select(Profile).where(Profile.id == profile_id))
        profile = result.scalar_one_or_none()

        if not profile:
            raise ProfileNotFoundError(profile_id)

        return self._profile_to_response(profile)

    async def list_profiles(
        self,
        db: AsyncSession,
        source: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ProfileListResponse:
        """List profiles."""
        query = select(Profile)

        if source:
            query = query.where(Profile.source == source)

        # Get total count
        count_query = select(func.count(Profile.id))
        if source:
            count_query = count_query.where(Profile.source == source)
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Get profiles
        query = query.order_by(Profile.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        profiles = result.scalars().all()

        items = [self._profile_to_response(p) for p in profiles]

        return ProfileListResponse(items=items, total=total)

    async def update_profile(
        self,
        db: AsyncSession,
        profile_id: str,
        profile_data: ProfileUpdate,
    ) -> ProfileResponse:
        """Update profile."""
        result = await db.execute(select(Profile).where(Profile.id == profile_id))
        profile = result.scalar_one_or_none()

        if not profile:
            raise ProfileNotFoundError(profile_id)

        # Update fields
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        await db.commit()
        await db.refresh(profile)

        return self._profile_to_response(profile)

    async def delete_profile(
        self,
        db: AsyncSession,
        profile_id: str,
    ) -> ProfileDeleteResponse:
        """Delete profile."""
        result = await db.execute(select(Profile).where(Profile.id == profile_id))
        profile = result.scalar_one_or_none()

        if not profile:
            raise ProfileNotFoundError(profile_id)

        await db.delete(profile)
        await db.commit()

        return ProfileDeleteResponse(id=profile_id, deleted=True)


profiles_service = ProfilesService()
