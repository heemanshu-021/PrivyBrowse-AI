"""
PrivyBrowse AI — Production Environment & System Configuration
Centralized configuration manager supporting strict environment variable ingestion,
validation, production-mode enforcement, and simulation-mode isolation.
"""

import os
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EnvironmentMode(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseModel):
    """Production application settings with strict validation."""
    
    # 1. Core Identity & Versioning
    app_name: str = "PrivyBrowse AI - On-Device Perception Backend"
    version: str = "1.0.0"
    env: EnvironmentMode = EnvironmentMode.PRODUCTION
    
    # 2. Network & Server Binding
    host: str = "127.0.0.1"
    port: int = 8000
    allowed_origins: List[str] = Field(default_factory=lambda: [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "chrome-extension://*"
    ])
    
    # 3. Execution & Simulation Isolation
    # CRITICAL: In production, simulation mode MUST default to False.
    # It requires explicit opt-in via PRIVYBROWSE_SIMULATION_MODE='true'/'1' for tests/offline dev only.
    simulation_mode: bool = False
    
    # 4. Perception & OCR Configuration
    ocr_enabled: bool = True
    tesseract_cmd: Optional[str] = None
    max_payload_bytes: int = 10 * 1024 * 1024  # 10 MB strict payload bound
    
    # 5. Security & Privacy
    enforce_pii_redaction: bool = True
    enforce_navigation_guard: bool = True
    enforce_injection_guard: bool = True
    
    # 6. Observability & Logging
    log_level: str = "INFO"
    event_buffer_capacity: int = 500
    
    @classmethod
    def load_from_env(cls) -> "Settings":
        """Loads and strictly validates settings from environment variables."""
        env_str = os.environ.get("PRIVYBROWSE_ENV", "production").lower().strip()
        try:
            env_mode = EnvironmentMode(env_str)
        except ValueError:
            env_mode = EnvironmentMode.PRODUCTION

        sim_raw = os.environ.get("PRIVYBROWSE_SIMULATION_MODE", "").lower().strip()
        sim_mode = sim_raw in ("true", "1", "yes", "enabled")

        host = os.environ.get("PRIVYBROWSE_HOST", "127.0.0.1").strip()
        try:
            port = int(os.environ.get("PRIVYBROWSE_PORT", "8000"))
        except ValueError:
            port = 8000

        tess_cmd = os.environ.get("TESSERACT_CMD") or None
        log_lvl = os.environ.get("PRIVYBROWSE_LOG_LEVEL", "INFO").upper().strip()

        # Origin parsing
        origins_raw = os.environ.get("PRIVYBROWSE_ALLOWED_ORIGINS")
        if origins_raw:
            origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
        else:
            origins = [
                "http://127.0.0.1:8000",
                "http://localhost:8000",
                "http://127.0.0.1:5173",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://localhost:3000",
                "chrome-extension://*"
            ]

        return cls(
            env=env_mode,
            host=host,
            port=port,
            simulation_mode=sim_mode,
            tesseract_cmd=tess_cmd,
            log_level=log_lvl,
            allowed_origins=origins
        )


# Global singleton settings instance
settings = Settings.load_from_env()


def get_settings() -> Settings:
    """Returns the active validated settings singleton."""
    return settings
