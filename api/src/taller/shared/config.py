"""Application configuration loaded from environment variables.

All settings are read from variables prefixed with ``TALLER_`` (for example
``TALLER_DATABASE_URL``), optionally supplied through an ``api/.env`` file
during local development.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#: Anchored to the `api/` package directory (not the process cwd), so
#: running tools (pytest, alembic, uvicorn) from another working directory
#: still reads `api/.env`. `config.py` lives at `api/src/taller/shared/`, so
#: `api/` is three parents up.
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Runtime configuration for the API.

    See ``api/env.example`` for the full list of supported variables.
    """

    model_config = SettingsConfigDict(
        env_prefix="TALLER_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://taller:taller@localhost:5440/taller"
    environment: str = "development"

    #: Secret used to sign session JWTs. Required (no default) so a real
    #: deployment can never fall back to a predictable secret.
    jwt_secret: str

    #: Whether the session cookie requires HTTPS (the ``Secure`` flag).
    #: Defaults to true; local dev/test environments set this to false.
    cookie_secure: bool = True

    @field_validator("jwt_secret")
    @classmethod
    def _jwt_secret_must_be_long_enough(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("TALLER_JWT_SECRET must be at least 32 characters long")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached :class:`Settings` instance."""
    return Settings()
