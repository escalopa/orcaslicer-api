"""Database models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class SliceJobStatus(str, enum.Enum):
    """Slice job status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Model(Base):
    """Uploaded model."""

    __tablename__ = "models"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    format = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    checksum_sha256 = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=func.now(), nullable=False)


class Profile(Base):
    """Slicing profile."""

    __tablename__ = "profiles"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    source = Column(String, nullable=False)  # "builtin" or "user"
    vendor = Column(String)
    machine_id = Column(String)
    process_id = Column(String)
    filament_id = Column(String)
    settings_overrides = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SliceJob(Base):
    """Slice job."""

    __tablename__ = "slice_jobs"

    id = Column(String, primary_key=True)
    model_id = Column(String, nullable=False)
    profile_id = Column(String, nullable=False)
    status = Column(SQLEnum(SliceJobStatus), nullable=False, default=SliceJobStatus.QUEUED)
    overrides = Column(JSON)
    output_options = Column(JSON)
    job_metadata = Column(JSON)

    queued_at = Column(DateTime, default=func.now(), nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

    progress_percent = Column(Integer)

    # Output data
    gcode_path = Column(String)
    project_3mf_path = Column(String)
    output_metadata = Column(JSON)

    # Error information
    error_message = Column(Text)
    error_details = Column(JSON)
