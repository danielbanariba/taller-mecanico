"""Application configuration loaded from environment variables.

All settings are read from variables prefixed with ``TALLER_`` (for example
``TALLER_DATABASE_URL``), optionally supplied through an ``api/.env`` file
during local development.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the API.

    See ``api/.env.example`` for the full list of supported variables.
    """

    model_config = SettingsConfigDict(
        env_prefix="TALLER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://taller:taller@localhost:5440/taller"
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached :class:`Settings` instance."""
    return Settings()
