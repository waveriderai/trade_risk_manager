"""
Application configuration using Pydantic settings.
Environment variables override defaults.
"""
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


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

    # CORS - accepts both string (comma-separated) and list
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8080"

    # Worker
    ENABLE_BACKGROUND_REFRESH: bool = False
    REFRESH_INTERVAL_MINUTES: int = 60

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse comma-separated origins into list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
