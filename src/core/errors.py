"""Custom exceptions and error handling."""

from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response model."""

    code: str
    message: str
    http_status: int
    details: Optional[Dict[str, Any]] = None


class ApiError(Exception):
    """Base API error."""

    def __init__(
        self,
        code: str,
        message: str,
        http_status: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.http_status = http_status
        self.details = details or {}
        super().__init__(message)


class ModelNotFoundError(ApiError):
    """Model not found."""

    def __init__(self, model_id: str):
        super().__init__(
            code="MODEL_NOT_FOUND",
            message=f"Model '{model_id}' does not exist.",
            http_status=status.HTTP_404_NOT_FOUND,
            details={"model_id": model_id},
        )


class ProfileNotFoundError(ApiError):
    """Profile not found."""

    def __init__(self, profile_id: str):
        super().__init__(
            code="PROFILE_NOT_FOUND",
            message=f"Profile '{profile_id}' does not exist or is not accessible.",
            http_status=status.HTTP_404_NOT_FOUND,
            details={"profile_id": profile_id},
        )


class SliceJobNotFoundError(ApiError):
    """Slice job not found."""

    def __init__(self, job_id: str):
        super().__init__(
            code="SLICE_JOB_NOT_FOUND",
            message=f"Slice job '{job_id}' does not exist.",
            http_status=status.HTTP_404_NOT_FOUND,
            details={"job_id": job_id},
        )


class UnsupportedFormatError(ApiError):
    """Unsupported file format."""

    def __init__(self, filename: str, format: str):
        super().__init__(
            code="UNSUPPORTED_FORMAT",
            message=f"File format '{format}' is not supported. Allowed: .stl, .step, .3mf.",
            http_status=status.HTTP_400_BAD_REQUEST,
            details={"filename": filename, "format": format},
        )


class SlicingError(ApiError):
    """Slicing operation failed."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="SLICING_FAILED",
            message=message,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details or {},
        )


class OrcaCliNotFoundError(ApiError):
    """OrcaSlicer CLI not found."""

    def __init__(self, path: str):
        super().__init__(
            code="ORCA_CLI_NOT_FOUND",
            message=f"OrcaSlicer CLI not found at '{path}'.",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"path": path},
        )


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    """Handle API errors."""
    return JSONResponse(
        status_code=exc.http_status,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "http_status": exc.http_status,
                "details": exc.details,
            }
        },
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "http_status": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "details": {"errors": exc.errors()},
            }
        },
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "http_status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "details": {"error": str(exc)},
            }
        },
    )
