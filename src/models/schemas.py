"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


# Model schemas
class ModelResponse(BaseModel):
    """Model response."""

    id: str
    filename: str
    format: str
    size_bytes: int
    uploaded_at: datetime
    checksum_sha256: str
    storage_path: str


class ModelListResponse(BaseModel):
    """Model list response."""

    items: List[ModelResponse]
    total: int


# Profile schemas
class ProfileCreate(BaseModel):
    """Create profile request."""

    name: str
    description: Optional[str] = None
    source: str = "user"
    vendor: Optional[str] = None
    machine_id: Optional[str] = None
    process_id: Optional[str] = None
    filament_id: Optional[str] = None
    settings_overrides: Optional[Dict[str, Any]] = None


class ProfileUpdate(BaseModel):
    """Update profile request."""

    name: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    machine_id: Optional[str] = None
    process_id: Optional[str] = None
    filament_id: Optional[str] = None
    settings_overrides: Optional[Dict[str, Any]] = None


class ProfileResponse(BaseModel):
    """Profile response."""

    id: str
    name: str
    description: Optional[str] = None
    source: str
    vendor: Optional[str] = None
    machine_id: Optional[str] = None
    process_id: Optional[str] = None
    filament_id: Optional[str] = None
    settings_overrides: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProfileListResponse(BaseModel):
    """Profile list response."""

    items: List[ProfileResponse]
    total: int


class ProfileDeleteResponse(BaseModel):
    """Profile delete response."""

    id: str
    deleted: bool


# Slice job schemas
class OutputOptions(BaseModel):
    """Output options for slice job."""

    model_config = ConfigDict(protected_namespaces=())

    gcode: bool = True
    project_3mf: bool = False
    metadata_json: bool = True


class SliceJobCreate(BaseModel):
    """Create slice job request."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    profile_id: str
    overrides: Optional[Dict[str, Any]] = None
    output_options: Optional[OutputOptions] = Field(default_factory=OutputOptions)
    metadata: Optional[Dict[str, Any]] = None


class BoundingBox(BaseModel):
    """Bounding box."""

    x: float
    y: float
    z: float


class SliceMetadata(BaseModel):
    """Slice output metadata."""

    estimated_print_time_seconds: Optional[int] = None
    model_print_time_seconds: Optional[int] = None
    first_layer_print_time_seconds: Optional[int] = None
    filament_used_mm: Optional[float] = None
    filament_used_g: Optional[float] = None
    filament_type: Optional[str] = None
    layer_count: Optional[int] = None
    bounding_box_mm: Optional[BoundingBox] = None


class SliceJobOutput(BaseModel):
    """Slice job output."""

    gcode_url: Optional[str] = None
    project_3mf_url: Optional[str] = None
    metadata: Optional[SliceMetadata] = None


class SliceJobResponse(BaseModel):
    """Slice job response."""

    model_config = ConfigDict(protected_namespaces=())

    id: str
    model_id: str
    profile_id: str
    status: str
    queued_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    progress_percent: Optional[int] = None
    overrides: Optional[Dict[str, Any]] = None
    output_options: Optional[Dict[str, Any]] = None
    output: Optional[SliceJobOutput] = None
    error_message: Optional[str] = None


# Health check schema
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    orca_cli_available: bool
    orca_version: Optional[str] = None
    profiles_loaded: int
    uptime_seconds: int
