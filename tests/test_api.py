"""
Basic API tests.

To run: pytest tests/
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "OrcaSlicer API"
    assert "version" in data


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "orca_cli_available" in data
    assert "profiles_loaded" in data
    assert "uptime_seconds" in data


def test_list_models_empty():
    """Test listing models when none exist."""
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_list_profiles():
    """Test listing profiles."""
    response = client.get("/profiles")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def test_create_profile():
    """Test creating a profile."""
    profile_data = {
        "name": "Test Profile",
        "description": "Test profile for unit tests",
        "source": "user",
        "vendor": "Test Vendor",
        "machine_id": "test_machine",
        "process_id": "test_process",
        "filament_id": "test_filament",
        "settings_overrides": {
            "layer_height": 0.2,
            "infill_density": 20
        }
    }

    response = client.post("/profiles", json=profile_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == profile_data["name"]
    assert data["source"] == "user"
    assert "id" in data

    # Cleanup
    profile_id = data["id"]
    client.delete(f"/profiles/{profile_id}")


def test_get_nonexistent_profile():
    """Test getting a profile that doesn't exist."""
    response = client.get("/profiles/nonexistent_id")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PROFILE_NOT_FOUND"


def test_error_response_format():
    """Test that error responses follow the standard format."""
    response = client.get("/profiles/invalid_id")
    assert response.status_code == 404
    data = response.json()

    # Check error structure
    assert "error" in data
    error = data["error"]
    assert "code" in error
    assert "message" in error
    assert "http_status" in error
    assert error["http_status"] == 404


def test_openapi_schema():
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
