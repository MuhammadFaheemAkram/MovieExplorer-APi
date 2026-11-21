"""Repositories: the only layer that builds and runs database queries."""

from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.genre_repository import GenreRepository
from app.repositories.movie_repository import MovieRepository

__all__ = ["FavoriteRepository", "GenreRepository", "MovieRepository"]
