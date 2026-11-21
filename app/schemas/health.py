"""Response schema for the health-check endpoint."""

from app.schemas.common import CamelModel


class HealthResponse(CamelModel):
    """Example JSON: {"status": "ok", "database": "ok"}"""

    status: str
    database: str
