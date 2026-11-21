"""
Application entry point - this is where the FastAPI app is created.

Run the server (from the project root, with the virtual env active):
    fastapi dev app/main.py

Then open:
    http://127.0.0.1:8000/docs   -> interactive Swagger UI (try every endpoint)
    http://127.0.0.1:8000/redoc  -> read-only API documentation

Android analogy: the `Application` class + `MainActivity` - it wires
everything together at startup.
"""

from fastapi import FastAPI

from app.api.router import api_router
from app.api.routes import health
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "REST API for the Movie Explorer app: browse, search, create and "
        "favorite movies. Built with FastAPI, SQLAlchemy 2.0 and PostgreSQL."
    ),
)

# Turn our custom errors (NotFoundError, ConflictError, ...) into JSON responses.
register_exception_handlers(app)

# /health stays outside the versioned prefix: it's about the server, not the API version.
app.include_router(health.router)

# All business endpoints: /api/v1/movies, /api/v1/favorites, ...
app.include_router(api_router, prefix=settings.api_v1_prefix)
