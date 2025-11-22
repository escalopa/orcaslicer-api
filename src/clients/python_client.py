"""Python client for OrcaSlicer API."""

from typing import Optional, Dict, Any, List
from pathlib import Path
import httpx


class ApiError(Exception):
    """API error exception."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{error_code}] {message}")


class OrcaSlicerClient:
    """
    Python client for OrcaSlicer API.

    Example usage:
        client = OrcaSlicerClient(base_url="http://localhost:8000")

        # Upload model
        model = client.upload_model("example.stl")

        # Create profile
        profile = client.create_profile({
            "name": "MyProfile",
            "vendor": "Ginger Additive",
            "machine_id": "ginger_large",
            "process_id": "0.2mm Quality",
            "filament_id": "PLA White",
            "settings_overrides": {"layer_height": 0.2}
        })

        # Create slice job
        job = client.create_slice_job(
            model_id=model["id"],
            profile_id=profile["id"],
            overrides={"infill_density": 30},
            output_options={"gcode": True, "project_3mf": True, "metadata_json": True}
        )

        # Wait for completion
        import time
        while True:
            job = client.get_slice_job(job["id"])
            if job["status"] in ["completed", "failed"]:
                break
            time.sleep(2)

        # Download results
        if job["status"] == "completed":
            client.download_gcode(job["id"], "output.gcode")
            client.download_project_3mf(job["id"], "project.3mf")
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize client.

        Args:
            base_url: Base URL of the API (e.g., "http://localhost:8000")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Any:
        """Make HTTP request and handle errors."""
        url = f"{self.base_url}{path}"
        response = self.client.request(method, url, **kwargs)

        if response.status_code >= 400:
            # Parse error response
            try:
                error_data = response.json().get("error", {})
                raise ApiError(
                    status_code=response.status_code,
                    error_code=error_data.get("code", "UNKNOWN_ERROR"),
                    message=error_data.get("message", "Unknown error occurred"),
                    details=error_data.get("details", {}),
                )
            except (KeyError, ValueError):
                raise ApiError(
                    status_code=response.status_code,
                    error_code="HTTP_ERROR",
                    message=f"HTTP {response.status_code}: {response.text}",
                )

        if response.status_code == 204:
            return None

        return response.json()

    def upload_model(
        self,
        path: str,
        original_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a 3D model file.

        Args:
            path: Path to the model file
            original_name: Original filename (defaults to basename of path)

        Returns:
            Model metadata dict with keys: id, filename, format, size_bytes,
            uploaded_at, checksum_sha256, storage_path
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        filename = original_name or file_path.name

        with open(file_path, "rb") as f:
            files = {"file": (filename, f)}
            return self._request("POST", "/models", files=files)

    def list_models(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List uploaded models.

        Args:
            limit: Maximum number of models to return
            offset: Number of models to skip

        Returns:
            List of model metadata dicts
        """
        response = self._request(
            "GET",
            "/models",
            params={"limit": limit, "offset": offset},
        )
        return response["items"]

    def get_model(self, model_id: str) -> Dict[str, Any]:
        """
        Get model details.

        Args:
            model_id: Model ID

        Returns:
            Model metadata dict
        """
        return self._request("GET", f"/models/{model_id}")

    def create_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new slicing profile.

        Args:
            profile: Profile data dict with keys: name, description, source,
                    vendor, machine_id, process_id, filament_id, settings_overrides

        Returns:
            Created profile dict
        """
        return self._request("POST", "/profiles", json=profile)

    def list_profiles(
        self,
        source: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List slicing profiles.

        Args:
            source: Filter by source ("builtin" or "user")
            limit: Maximum number of profiles to return
            offset: Number of profiles to skip

        Returns:
            List of profile dicts
        """
        params = {"limit": limit, "offset": offset}
        if source:
            params["source"] = source

        response = self._request("GET", "/profiles", params=params)
        return response["items"]

    def get_profile(self, profile_id: str) -> Dict[str, Any]:
        """
        Get profile details.

        Args:
            profile_id: Profile ID

        Returns:
            Profile dict
        """
        return self._request("GET", f"/profiles/{profile_id}")

    def update_profile(
        self,
        profile_id: str,
        patch: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Update a profile.

        Args:
            profile_id: Profile ID
            patch: Partial profile data to update

        Returns:
            Updated profile dict
        """
        return self._request("PATCH", f"/profiles/{profile_id}", json=patch)

    def delete_profile(self, profile_id: str) -> None:
        """
        Delete a profile.

        Args:
            profile_id: Profile ID
        """
        self._request("DELETE", f"/profiles/{profile_id}")

    def create_slice_job(
        self,
        model_id: str,
        profile_id: str,
        overrides: Optional[Dict[str, Any]] = None,
        output_options: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new slice job.

        Args:
            model_id: Model ID to slice
            profile_id: Profile ID to use
            overrides: Per-request setting overrides
            output_options: Output options (gcode, project_3mf, metadata_json)
            metadata: Custom metadata for the job

        Returns:
            Created slice job dict
        """
        job_data = {
            "model_id": model_id,
            "profile_id": profile_id,
        }

        if overrides:
            job_data["overrides"] = overrides
        if output_options:
            job_data["output_options"] = output_options
        if metadata:
            job_data["metadata"] = metadata

        return self._request("POST", "/slice-jobs", json=job_data)

    def get_slice_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get slice job status and results.

        Args:
            job_id: Job ID

        Returns:
            Slice job dict with status and output (if completed)
        """
        return self._request("GET", f"/slice-jobs/{job_id}")

    def download_gcode(self, job_id: str, dest_path: str) -> None:
        """
        Download G-code output.

        Args:
            job_id: Job ID
            dest_path: Destination file path
        """
        url = f"{self.base_url}/slice-jobs/{job_id}/gcode"
        response = self.client.get(url)

        if response.status_code >= 400:
            try:
                error_data = response.json().get("error", {})
                raise ApiError(
                    status_code=response.status_code,
                    error_code=error_data.get("code", "UNKNOWN_ERROR"),
                    message=error_data.get("message", "Unknown error occurred"),
                    details=error_data.get("details", {}),
                )
            except (KeyError, ValueError):
                raise ApiError(
                    status_code=response.status_code,
                    error_code="HTTP_ERROR",
                    message=f"HTTP {response.status_code}: {response.text}",
                )

        with open(dest_path, "wb") as f:
            f.write(response.content)

    def download_project_3mf(self, job_id: str, dest_path: str) -> None:
        """
        Download 3MF project file.

        Args:
            job_id: Job ID
            dest_path: Destination file path
        """
        url = f"{self.base_url}/slice-jobs/{job_id}/project.3mf"
        response = self.client.get(url)

        if response.status_code >= 400:
            try:
                error_data = response.json().get("error", {})
                raise ApiError(
                    status_code=response.status_code,
                    error_code=error_data.get("code", "UNKNOWN_ERROR"),
                    message=error_data.get("message", "Unknown error occurred"),
                    details=error_data.get("details", {}),
                )
            except (KeyError, ValueError):
                raise ApiError(
                    status_code=response.status_code,
                    error_code="HTTP_ERROR",
                    message=f"HTTP {response.status_code}: {response.text}",
                )

        with open(dest_path, "wb") as f:
            f.write(response.content)

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.close()
