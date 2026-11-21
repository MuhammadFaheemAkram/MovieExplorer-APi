"""Pydantic schemas: the shape of JSON request and response bodies."""

from app.schemas.health import HealthResponse
from app.schemas.movie import MovieCreate, MovieListResponse, MovieResponse, MovieUpdate

__all__ = ["HealthResponse", "MovieCreate", "MovieListResponse", "MovieResponse", "MovieUpdate"]
