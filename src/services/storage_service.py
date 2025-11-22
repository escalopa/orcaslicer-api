"""Storage service for file operations."""

import hashlib
import shutil
from pathlib import Path
from typing import BinaryIO
from ..core.config import settings


class StorageService:
    """Handle file storage operations."""

    def __init__(self):
        self.models_dir = settings.models_dir
        self.outputs_dir = settings.outputs_dir
        self.work_dir = settings.work_dir

    def save_model(self, model_id: str, file: BinaryIO, filename: str) -> tuple[str, int, str]:
        """
        Save uploaded model file.

        Returns: (storage_path, size_bytes, checksum_sha256)
        """
        model_dir = self.models_dir / model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        file_path = model_dir / filename

        # Calculate hash while saving
        sha256_hash = hashlib.sha256()
        size_bytes = 0

        with open(file_path, "wb") as f:
            while chunk := file.read(8192):
                f.write(chunk)
                sha256_hash.update(chunk)
                size_bytes += len(chunk)

        return str(file_path), size_bytes, sha256_hash.hexdigest()

    def get_model_path(self, model_id: str) -> Path:
        """Get model directory path."""
        return self.models_dir / model_id

    def get_job_output_dir(self, job_id: str) -> Path:
        """Get or create job output directory."""
        output_dir = self.outputs_dir / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def get_job_work_dir(self, job_id: str) -> Path:
        """Get or create job working directory."""
        work_dir = self.work_dir / job_id
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir

    def cleanup_work_dir(self, job_id: str):
        """Clean up job working directory."""
        work_dir = self.work_dir / job_id
        if work_dir.exists():
            shutil.rmtree(work_dir)

    def get_file_path(self, job_id: str, filename: str) -> Path:
        """Get output file path."""
        return self.outputs_dir / job_id / filename


storage_service = StorageService()
