"""Model upload and management routes."""

from fastapi import APIRouter, UploadFile, File, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..models.schemas import ModelResponse, ModelListResponse
from ..services.models_service import models_service


router = APIRouter(prefix="/models", tags=["models"])


@router.post("", response_model=ModelResponse, status_code=201)
async def upload_model(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a 3D model file.

    Supported formats: .stl, .step, .3mf
    """
    return await models_service.upload_model(
        db=db,
        file=file.file,
        filename=file.filename,
        original_name=file.filename,
    )


@router.get("", response_model=ModelListResponse)
async def list_models(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List uploaded models."""
    return await models_service.list_models(db=db, limit=limit, offset=offset)


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get model details by ID."""
    return await models_service.get_model(db=db, model_id=model_id)
