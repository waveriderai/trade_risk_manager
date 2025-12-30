"""
Application configuration using Pydantic settings.
Environment variables override defaults.
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "WaveRider Trading Journal"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://waverider:waverider_password@localhost:5432/waverider_db"

    # Market Data
    POLYGON_API_KEY: str = ""

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Worker
    ENABLE_BACKGROUND_REFRESH: bool = False
    REFRESH_INTERVAL_MINUTES: int = 60

    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse comma-separated origins into list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
