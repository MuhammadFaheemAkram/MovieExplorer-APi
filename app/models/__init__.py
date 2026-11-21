"""
Import every model here.

Two reasons:
  1. Other code can write `from app.models import Movie, Genre, Favorite`.
  2. Alembic imports this package to discover ALL tables. A model that is never
     imported is invisible to Alembic and would be missing from migrations.
"""

from app.models.base import Base
from app.models.favorite import Favorite
from app.models.genre import Genre
from app.models.movie import Movie, movie_genres

# __all__ lists the names this package "exports".
__all__ = ["Base", "Favorite", "Genre", "Movie", "movie_genres"]
