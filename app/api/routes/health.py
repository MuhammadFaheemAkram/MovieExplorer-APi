"""
Health check: a tiny endpoint that says "the API is up and can reach the database".
Used by monitoring tools, load balancers, Docker, or just you in the browser.
"""

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: DbSession):
    """Return `ok` if the API is running and PostgreSQL answers a trivial query."""
    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        database_status = "unavailable"

    return HealthResponse(status="ok", database=database_status)
