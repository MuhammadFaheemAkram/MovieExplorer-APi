"""
Collects all versioned routers into one `api_router`.
main.py mounts it under /api/v1, so `/movies` becomes `/api/v1/movies`.

To add a new feature later (e.g. genres), create app/api/routes/genres.py
and add one `include_router` line here.
"""

from fastapi import APIRouter

from app.api.routes import favorites, movies

api_router = APIRouter()
api_router.include_router(movies.router)
api_router.include_router(favorites.router)
