"""
Application settings.

All configuration (database URL, debug flag, ...) lives in ONE place: the
`Settings` class below. Values are read automatically from environment
variables or from the `.env` file in the project root.

Android analogy: this is like `BuildConfig` / `local.properties` - values that
change per environment (dev, staging, production) and must never be hard-coded.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path of the project root folder (movie-explorer-api/).
# __file__ is this file: app/core/config.py -> go up 3 levels.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Each attribute maps to an environment variable with the same name
    (case-insensitive). Example: `database_url` <- DATABASE_URL.

    Pydantic validates the types for us: if DEBUG=hello is in .env,
    the app refuses to start with a clear error instead of failing later.
    """

    app_name: str = "Movie Explorer API"
    debug: bool = False

    # No default value -> this setting is REQUIRED. The app will not start without it.
    database_url: str

    # Only needed when running the tests (pytest).
    test_database_url: str | None = None

    # Connection pool size. pool_size + max_overflow must be AT LEAST FastAPI's
    # worker-thread count (40), otherwise a burst of requests can deadlock
    # (see app/core/database.py). PostgreSQL allows 100 connections by default.
    db_pool_size: int = 20
    db_max_overflow: int = 20

    # All business endpoints are grouped under this prefix, e.g. /api/v1/movies.
    # Versioning lets you ship /api/v2 later without breaking old app versions.
    api_v1_prefix: str = "/api/v1"

    # Tell pydantic-settings where the .env file is.
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )


# A single shared settings object. Other files simply do:
#     from app.core.config import settings
settings = Settings()
