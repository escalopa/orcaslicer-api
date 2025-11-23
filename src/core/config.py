"""Application configuration."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API settings
    api_title: str = "OrcaSlicer API"
    api_version: str = "1.0.0"
    api_description: str = "HTTP API wrapper for OrcaSlicer"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # OrcaSlicer settings
    orca_cli_path: str = os.getenv("ORCA_CLI_PATH", "/usr/local/bin/orcaslicer")
    orca_datadir: str = os.getenv("ORCA_DATADIR", "/app/orca-config")

    # Storage settings
    data_dir: Path = Path(os.getenv("DATA_DIR", "/data"))
    models_dir: Path = data_dir / "models"
    outputs_dir: Path = data_dir / "outputs"
    work_dir: Path = data_dir / "work"

    # Database settings
    database_url: str = f"sqlite+aiosqlite:///{data_dir}/orcaslicer.db"

    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_json: bool = os.getenv("LOG_JSON", "true").lower() == "true"

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False

    def setup_directories(self):
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.setup_directories()
