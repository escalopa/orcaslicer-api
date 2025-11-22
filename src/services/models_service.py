"""Model management service."""

import secrets
from pathlib import Path
from typing import BinaryIO, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.db_models import Model
from ..models.schemas import ModelResponse, ModelListResponse
from ..core.errors import ModelNotFoundError, UnsupportedFormatError
from .storage_service import storage_service


SUPPORTED_FORMATS = {".stl", ".step", ".3mf"}


class ModelsService:
    """Service for managing uploaded models."""

    @staticmethod
    def _generate_model_id() -> str:
        """Generate unique model ID."""
        return f"mdl_{secrets.token_hex(4)}"

    @staticmethod
    def _get_file_format(filename: str) -> str:
        """Extract file format from filename."""
        return Path(filename).suffix.lower().lstrip(".")

    async def upload_model(
        self,
        db: AsyncSession,
        file: BinaryIO,
        filename: str,
        original_name: Optional[str] = None,
    ) -> ModelResponse:
        """Upload a new model."""
        # Validate format
        file_format = self._get_file_format(filename)
        if f".{file_format}" not in SUPPORTED_FORMATS:
            raise UnsupportedFormatError(filename, f".{file_format}")

        # Generate model ID
        model_id = self._generate_model_id()

        # Save file
        storage_path, size_bytes, checksum = storage_service.save_model(
            model_id, file, filename
        )

        # Create database record
        model = Model(
            id=model_id,
            filename=original_name or filename,
            format=file_format,
            size_bytes=size_bytes,
            checksum_sha256=checksum,
            storage_path=storage_path,
        )

        db.add(model)
        await db.commit()
        await db.refresh(model)

        return ModelResponse(
            id=model.id,
            filename=model.filename,
            format=model.format,
            size_bytes=model.size_bytes,
            uploaded_at=model.uploaded_at,
            checksum_sha256=model.checksum_sha256,
            storage_path=model.storage_path,
        )

    async def get_model(self, db: AsyncSession, model_id: str) -> ModelResponse:
        """Get model by ID."""
        result = await db.execute(select(Model).where(Model.id == model_id))
        model = result.scalar_one_or_none()

        if not model:
            raise ModelNotFoundError(model_id)

        return ModelResponse(
            id=model.id,
            filename=model.filename,
            format=model.format,
            size_bytes=model.size_bytes,
            uploaded_at=model.uploaded_at,
            checksum_sha256=model.checksum_sha256,
            storage_path=model.storage_path,
        )

    async def list_models(
        self,
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> ModelListResponse:
        """List all models."""
        # Get total count
        count_result = await db.execute(select(func.count(Model.id)))
        total = count_result.scalar_one()

        # Get models
        result = await db.execute(
            select(Model).order_by(Model.uploaded_at.desc()).limit(limit).offset(offset)
        )
        models = result.scalars().all()

        items = [
            ModelResponse(
                id=m.id,
                filename=m.filename,
                format=m.format,
                size_bytes=m.size_bytes,
                uploaded_at=m.uploaded_at,
                checksum_sha256=m.checksum_sha256,
                storage_path=m.storage_path,
            )
            for m in models
        ]

        return ModelListResponse(items=items, total=total)


models_service = ModelsService()
