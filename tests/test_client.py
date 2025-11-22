"""
Tests for the Python client.

These tests require a running API instance.
To run: pytest tests/test_client.py --api-url http://localhost:8000
"""

import pytest
from src.clients.python_client import OrcaSlicerClient, ApiError


@pytest.fixture
def client():
    """Create a test client."""
    return OrcaSlicerClient(base_url="http://localhost:8000")


def test_client_initialization():
    """Test client initialization."""
    client = OrcaSlicerClient(base_url="http://localhost:8000")
    assert client.base_url == "http://localhost:8000"
    assert client.timeout == 30.0


def test_list_profiles(client):
    """Test listing profiles."""
    profiles = client.list_profiles()
    assert isinstance(profiles, list)


def test_create_and_delete_profile(client):
    """Test creating and deleting a profile."""
    profile_data = {
        "name": "Test Client Profile",
        "description": "Created by test client",
        "source": "user",
        "vendor": "Test",
        "machine_id": "test_machine",
        "process_id": "test_process",
        "filament_id": "test_filament",
        "settings_overrides": {"layer_height": 0.2}
    }

    # Create
    profile = client.create_profile(profile_data)
    assert profile["name"] == profile_data["name"]
    profile_id = profile["id"]

    # Get
    retrieved = client.get_profile(profile_id)
    assert retrieved["id"] == profile_id

    # Delete
    client.delete_profile(profile_id)

    # Verify deletion
    with pytest.raises(ApiError) as exc_info:
        client.get_profile(profile_id)
    assert exc_info.value.error_code == "PROFILE_NOT_FOUND"


def test_api_error_handling(client):
    """Test that API errors are properly raised."""
    with pytest.raises(ApiError) as exc_info:
        client.get_profile("nonexistent_profile_id")

    error = exc_info.value
    assert error.status_code == 404
    assert error.error_code == "PROFILE_NOT_FOUND"
    assert "nonexistent_profile_id" in error.message
