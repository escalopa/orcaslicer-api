"""Slicing service - orchestrates OrcaSlicer CLI calls."""

import asyncio
import json
import math
import re
import secrets
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.db_models import SliceJob, SliceJobStatus, Model, Profile
from ..models.schemas import (
    SliceJobCreate,
    SliceJobResponse,
    SliceJobOutput,
    SliceMetadata,
    BoundingBox,
)
from ..core.config import settings
from ..core.errors import (
    SliceJobNotFoundError,
    ModelNotFoundError,
    ProfileNotFoundError,
    SlicingError,
    OrcaCliNotFoundError,
)
from ..core.logging import logger
from .storage_service import storage_service


class SliceService:
    """Service for managing slice jobs and OrcaSlicer CLI integration."""

    @staticmethod
    def _generate_job_id() -> str:
        """Generate unique job ID."""
        return f"job_{secrets.token_hex(4)}"

    @staticmethod
    def _check_orca_cli() -> bool:
        """Check if OrcaSlicer CLI is available."""
        return Path(settings.orca_cli_path).exists()

    async def create_slice_job(
        self,
        db: AsyncSession,
        job_data: SliceJobCreate,
    ) -> SliceJobResponse:
        """Create a new slice job."""
        # Validate model exists
        model_result = await db.execute(
            select(Model).where(Model.id == job_data.model_id)
        )
        model = model_result.scalar_one_or_none()
        if not model:
            raise ModelNotFoundError(job_data.model_id)

        # Validate profile exists
        profile_result = await db.execute(
            select(Profile).where(Profile.id == job_data.profile_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            raise ProfileNotFoundError(job_data.profile_id)

        # Create job
        job_id = self._generate_job_id()
        job = SliceJob(
            id=job_id,
            model_id=job_data.model_id,
            profile_id=job_data.profile_id,
            status=SliceJobStatus.QUEUED,
            overrides=job_data.overrides,
            output_options=job_data.output_options.model_dump() if job_data.output_options else {},
            job_metadata=job_data.metadata,
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        # Start background slicing task
        asyncio.create_task(self._process_slice_job(job_id, model.storage_path, profile))

        return self._job_to_response(job)

    async def get_slice_job(
        self,
        db: AsyncSession,
        job_id: str,
    ) -> SliceJobResponse:
        """Get slice job by ID."""
        result = await db.execute(select(SliceJob).where(SliceJob.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            raise SliceJobNotFoundError(job_id)

        return self._job_to_response(job)

    def _job_to_response(self, job: SliceJob) -> SliceJobResponse:
        """Convert SliceJob to response."""
        output = None
        if job.status == SliceJobStatus.COMPLETED and job.output_metadata:
            # Build output URLs
            base_url = f"http://localhost:{settings.port}"  # TODO: Make configurable
            output = SliceJobOutput(
                gcode_url=f"{base_url}/files/{job.id}/output.gcode" if job.gcode_path else None,
                project_3mf_url=f"{base_url}/files/{job.id}/project.3mf" if job.project_3mf_path else None,
                metadata=SliceMetadata(**job.output_metadata) if job.output_metadata else None,
            )

        return SliceJobResponse(
            id=job.id,
            model_id=job.model_id,
            profile_id=job.profile_id,
            status=job.status.value,
            queued_at=job.queued_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            progress_percent=job.progress_percent,
            overrides=job.overrides,
            output_options=job.output_options,
            output=output,
            error_message=job.error_message,
        )

    async def _process_slice_job(
        self,
        job_id: str,
        model_path: str,
        profile: Profile,
    ):
        """Process a slice job in the background."""
        from ..database import async_session_maker

        async with async_session_maker() as db:
            try:
                # Update job status to running
                result = await db.execute(select(SliceJob).where(SliceJob.id == job_id))
                job = result.scalar_one()
                job.status = SliceJobStatus.RUNNING
                job.started_at = datetime.utcnow()
                await db.commit()

                logger.info(f"Starting slice job {job_id}", extra={
                    "job_id": job_id,
                    "model_id": job.model_id,
                    "profile_id": job.profile_id,
                })

                # Check OrcaSlicer CLI
                if not self._check_orca_cli():
                    raise OrcaCliNotFoundError(settings.orca_cli_path)

                # Prepare working directory
                work_dir = storage_service.get_job_work_dir(job_id)
                output_dir = storage_service.get_job_output_dir(job_id)

                # Build OrcaSlicer command
                cmd = await self._build_orca_command(
                    model_path,
                    work_dir,
                    output_dir,
                    profile,
                    job.overrides or {},
                    job.output_options or {},
                )

                # Execute OrcaSlicer
                logger.info(f"Executing OrcaSlicer: {' '.join(cmd)}")
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(work_dir),
                )

                stdout, stderr = await process.communicate()

                stdout_text = stdout.decode() if stdout else ""
                stderr_text = stderr.decode() if stderr else ""

                if process.returncode != 0:
                    logger.error(
                        f"OrcaSlicer failed with exit code {process.returncode}",
                        extra={
                            "job_id": job_id,
                            "exit_code": process.returncode,
                            "command": ' '.join(cmd),
                            "stdout": stdout_text[:500],
                            "stderr": stderr_text[:500],
                        }
                    )
                    raise SlicingError(
                        f"OrcaSlicer exited with code {process.returncode}: {stderr_text[:200]}",
                        details={
                            "exit_code": process.returncode,
                            "stderr": stderr_text,
                            "stdout": stdout_text,
                            "command": ' '.join(cmd),
                        },
                    )

                logger.info(f"OrcaSlicer completed successfully", extra={
                    "job_id": job_id,
                    "stdout": stdout_text[:200] if stdout_text else "No output",
                })

                # Parse outputs and generate metadata
                metadata = await self._generate_metadata(output_dir, job.output_options or {})

                # Update job with results
                await db.refresh(job)
                job.status = SliceJobStatus.COMPLETED
                job.finished_at = datetime.utcnow()
                job.progress_percent = 100

                # Find generated gcode file (OrcaSlicer names it based on input file)
                if (job.output_options or {}).get("gcode", True):
                    gcode_files = list(output_dir.glob("*.gcode"))
                    if gcode_files:
                        # Rename to standardized name for easier access
                        gcode_output = output_dir / "output.gcode"
                        gcode_files[0].rename(gcode_output)
                        job.gcode_path = str(gcode_output)
                    else:
                        logger.warning(f"No gcode file found in {output_dir}")

                if (job.output_options or {}).get("project_3mf", False):
                    job.project_3mf_path = str(output_dir / "project.3mf")

                job.output_metadata = metadata
                await db.commit()

                # Cleanup work directory
                storage_service.cleanup_work_dir(job_id)

                logger.info(f"Slice job {job_id} completed successfully")

            except Exception as e:
                logger.exception(f"Slice job {job_id} failed")

                # Update job with error
                result = await db.execute(select(SliceJob).where(SliceJob.id == job_id))
                job = result.scalar_one_or_none()
                if job:
                    job.status = SliceJobStatus.FAILED
                    job.finished_at = datetime.utcnow()
                    job.error_message = str(e)
                    job.error_details = {"error": str(e)}
                    await db.commit()

    async def _build_orca_command(
        self,
        model_path: str,
        work_dir: Path,
        output_dir: Path,
        profile: Profile,
        overrides: Dict[str, Any],
        output_options: Dict[str, Any],
    ) -> list[str]:
        """Build OrcaSlicer CLI command."""
        cmd = [settings.orca_cli_path]

        # Set data directory first if provided
        # This directory should contain machine/, process/, and filament/ subdirectories with profile JSONs
        if settings.orca_datadir:
            cmd.extend(["--datadir", settings.orca_datadir])

        # Set output directory
        cmd.extend(["--outputdir", str(output_dir)])

        # Create settings file with profile and overrides if there are any settings
        if profile.settings_overrides or overrides:
            settings_file = await self._create_settings_file(work_dir, profile, overrides)
            if settings_file:
                cmd.extend(["--load-settings", str(settings_file)])

        # Add slice flag (0 = slice all plates)
        cmd.extend(["--slice", "0"])

        # Export 3MF if requested
        if output_options.get("project_3mf", False):
            cmd.extend(["--export-3mf", str(output_dir / "project.3mf")])

        # Add model input (must be last or near last)
        cmd.append(model_path)

        logger.debug(f"Built OrcaSlicer command: {' '.join(cmd)}")

        return cmd

    async def _create_settings_file(
        self,
        work_dir: Path,
        profile: Profile,
        overrides: Dict[str, Any],
    ) -> Optional[Path]:
        """Create a settings JSON file for OrcaSlicer.

        OrcaSlicer requires specific metadata fields in the JSON:
        - type: "machine", "process", or "filament"
        - name: preset name
        - from: "system", "User", or "user"
        - version: version string (optional)
        """
        # Start with OrcaSlicer required metadata
        settings_data = {
            "type": "process",  # Default to process settings
            "name": profile.name or "API Generated Profile",
            "from": "user",  # Mark as user-generated
            "version": "1.0.0",
        }

        # Add profile settings
        if profile.settings_overrides:
            settings_data.update(profile.settings_overrides)

        # Apply job-specific overrides
        if overrides:
            settings_data.update(overrides)

        # Convert settings to OrcaSlicer expected types
        settings_data = self._convert_settings_types(settings_data)

        # Ensure layer_gcode has G92 E0 to fix the relative extruder error
        if "layer_gcode" not in settings_data:
            settings_data["layer_gcode"] = "G92 E0"
        elif isinstance(settings_data["layer_gcode"], str) and "G92 E0" not in settings_data["layer_gcode"]:
            settings_data["layer_gcode"] = settings_data["layer_gcode"] + "\nG92 E0"

        # Write settings to file
        settings_file = work_dir / "settings.json"
        with open(settings_file, "w") as f:
            json.dump(settings_data, f, indent=2)

        logger.debug(f"Created settings file with metadata: type={settings_data.get('type')}, name={settings_data.get('name')}, from={settings_data.get('from')}")
        return settings_file

    def _convert_settings_types(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Convert settings values to OrcaSlicer expected types.

        OrcaSlicer expects specific string formats for many settings:
        - Numeric values like layer_height should be strings (e.g., "0.2")
        - Percent values should have % suffix (e.g., "25%")
        - Boolean values should be "0" or "1" strings
        """
        result = settings.copy()

        # Settings that should be string representations of numbers
        numeric_string_settings = {
            "layer_height",
            "initial_layer_print_height",
            "line_width",
            "inner_wall_line_width",
            "outer_wall_line_width",
            "top_surface_line_width",
            "sparse_infill_line_width",
            "support_line_width",
            "first_layer_extrusion_width",
            "min_layer_height",
            "max_layer_height",
        }

        # Settings that should be percent strings (e.g., "25%")
        percent_settings = {
            "sparse_infill_density",
            "infill_density",  # Alias - will be converted to sparse_infill_density
            "internal_bridge_density",
            "skin_infill_density",
            "skeleton_infill_density",
        }

        # Settings that should be "0" or "1" strings for booleans
        bool_string_settings = {
            "enable_support",
            "detect_thin_wall",
            "only_one_wall_top",
            "spiral_mode",
            "overhang_reverse",
        }

        # Handle infill_density -> sparse_infill_density alias
        if "infill_density" in result and "sparse_infill_density" not in result:
            result["sparse_infill_density"] = result.pop("infill_density")

        for key, value in list(result.items()):
            if value is None:
                continue

            # Convert numeric values to strings for specific settings
            if key in numeric_string_settings:
                if isinstance(value, (int, float)):
                    result[key] = str(value)

            # Convert percent values - add % if missing
            elif key in percent_settings:
                if isinstance(value, (int, float)):
                    result[key] = f"{value}%"
                elif isinstance(value, str) and not value.endswith("%"):
                    result[key] = f"{value}%"

            # Convert booleans to "0" or "1" strings
            elif key in bool_string_settings:
                if isinstance(value, bool):
                    result[key] = "1" if value else "0"
                elif isinstance(value, int):
                    result[key] = str(value)

        return result

    async def _generate_metadata(
        self,
        output_dir: Path,
        output_options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate metadata from slice outputs.

        Extracts metadata from:
        - G-code file: print time, layer count, dimensions
        - 3MF file (if available): filament usage data from embedded XML
        """
        metadata: Dict[str, Any] = {}

        try:
            # Find the gcode file
            gcode_file = output_dir / "output.gcode"
            if not gcode_file.exists():
                # Try to find any gcode file
                gcode_files = list(output_dir.glob("*.gcode"))
                if gcode_files:
                    gcode_file = gcode_files[0]
                else:
                    logger.warning(f"No gcode file found in {output_dir}")
                    return metadata

            # Parse gcode metadata
            gcode_metadata = await self._parse_gcode_metadata(gcode_file)
            metadata.update(gcode_metadata)

            # If 3MF was generated, extract filament data from it
            project_3mf = output_dir / "project.3mf"
            if project_3mf.exists():
                filament_metadata = await self._parse_3mf_metadata(project_3mf, output_dir)
                metadata.update(filament_metadata)

            logger.info(f"Extracted metadata: {metadata}")

        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}", exc_info=True)

        return metadata

    async def _parse_gcode_metadata(self, gcode_file: Path) -> Dict[str, Any]:
        """Parse metadata from gcode file.

        Extracts:
        - Print times (total, model, first layer)
        - Max Z height
        - Layer count
        """
        metadata: Dict[str, Any] = {}

        try:
            with open(gcode_file, 'r', encoding='utf-8') as f:
                gcode_content = f.read()

            # Extract print times
            # Format: "; total estimated time: 1h 16m 56s"
            total_time_match = re.search(r"total estimated time:\s+([0-9hms\s]+)", gcode_content)
            if total_time_match:
                total_time_str = total_time_match.group(1).strip()
                metadata["estimated_print_time_seconds"] = self._time_string_to_seconds(total_time_str)

            # Extract model printing time
            # Format: "; model printing time: 1h 15m 23s ;"
            model_time_match = re.search(r"model printing time:\s+([0-9hms\s]+);", gcode_content)
            if model_time_match:
                model_time_str = model_time_match.group(1).strip()
                metadata["model_print_time_seconds"] = self._time_string_to_seconds(model_time_str)

            # Extract first layer printing time
            # Format: "; first layer printing time = 4m 23s"
            first_layer_time_match = re.search(r"first layer printing time.*?=\s+([0-9hms\s]+)", gcode_content)
            if first_layer_time_match:
                first_layer_time_str = first_layer_time_match.group(1).strip()
                metadata["first_layer_print_time_seconds"] = self._time_string_to_seconds(first_layer_time_str)

            # Extract max Z height
            # Format: "; max_z_height: 35.4"
            max_z_match = re.search(r"max_z_height:\s+([0-9.]+)", gcode_content)
            if max_z_match:
                max_z = float(max_z_match.group(1))
                metadata["bounding_box_mm"] = {"z": max_z}

            # Count layers by counting layer change comments
            # OrcaSlicer uses "; CHANGE_LAYER" or similar
            layer_changes = re.findall(r";\s*CHANGE_LAYER", gcode_content)
            if layer_changes:
                metadata["layer_count"] = len(layer_changes)
            else:
                # Alternative: count "; layer" comments
                layer_comments = re.findall(r";\s*layer\s+\d+", gcode_content, re.IGNORECASE)
                if layer_comments:
                    metadata["layer_count"] = len(layer_comments)

            logger.debug(f"Extracted gcode metadata: {metadata}")

        except Exception as e:
            logger.error(f"Failed to parse gcode metadata: {e}", exc_info=True)

        return metadata

    async def _parse_3mf_metadata(self, project_3mf: Path, output_dir: Path) -> Dict[str, Any]:
        """Parse filament metadata from 3MF file.

        The 3MF file is actually a zip archive containing:
        - Metadata/slice_info.config (XML with filament data)
        """
        metadata: Dict[str, Any] = {}

        try:
            # Create a temporary directory for extraction
            temp_extract_dir = output_dir / "temp_3mf_extract"
            temp_extract_dir.mkdir(exist_ok=True)

            # Extract the 3MF (which is actually a zip file)
            with zipfile.ZipFile(project_3mf, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)

            # Parse the slice_info.config XML file
            slice_info_path = temp_extract_dir / "Metadata" / "slice_info.config"
            if slice_info_path.exists():
                with open(slice_info_path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()

                # Parse XML
                root = ET.fromstring(xml_content)

                # Extract filament info from plate/filament element
                plate = root.find("plate")
                if plate is not None:
                    filament = plate.find("filament")
                    if filament is not None:
                        # Extract filament usage in meters
                        used_m = filament.attrib.get("used_m")
                        if used_m:
                            metadata["filament_used_mm"] = float(used_m) * 1000  # Convert to mm

                        # Extract filament usage in grams
                        used_g = filament.attrib.get("used_g")
                        if used_g:
                            metadata["filament_used_g"] = float(used_g)

                        # Optionally extract filament type
                        filament_type = filament.attrib.get("type")
                        if filament_type:
                            metadata["filament_type"] = filament_type

                logger.debug(f"Extracted 3MF metadata: {metadata}")

            # Cleanup temp directory
            shutil.rmtree(temp_extract_dir, ignore_errors=True)

        except Exception as e:
            logger.error(f"Failed to parse 3MF metadata: {e}", exc_info=True)
            # Cleanup on error
            temp_extract_dir = output_dir / "temp_3mf_extract"
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir, ignore_errors=True)

        return metadata

    def _time_string_to_seconds(self, time_str: str) -> int:
        """Convert time string like '1h 16m 56s' to total seconds.

        Args:
            time_str: Time string in format like "1h 16m 56s", "23m 45s", or "56s"

        Returns:
            Total time in seconds (rounded up)
        """
        h = m = s = 0

        # Extract hours
        h_match = re.search(r'(\d+)h', time_str)
        if h_match:
            h = int(h_match.group(1))

        # Extract minutes
        m_match = re.search(r'(\d+)m', time_str)
        if m_match:
            m = int(m_match.group(1))

        # Extract seconds
        s_match = re.search(r'(\d+)s', time_str)
        if s_match:
            s = int(s_match.group(1))

        # Calculate total seconds (round up if there are any seconds)
        total_seconds = h * 3600 + m * 60 + s
        return total_seconds


slice_service = SliceService()
