"""
FavoriteService: business logic for the favorites list.

Design choice - "idempotent" add/remove:
    Adding a movie that is already a favorite is NOT an error; it simply stays
    a favorite. Removing a movie that is not a favorite is also fine.
    Calling the same request twice gives the same result, which makes the
    mobile app simpler and safe to retry on a flaky network.
"""

from sqlalchemy.orm import Session

from app.models import Movie
from app.repositories import FavoriteRepository
from app.schemas import MovieListResponse
from app.services.movie_service import MovieService


class FavoriteService:
    def __init__(self, db: Session):
        self.db = db
        self.favorite_repository = FavoriteRepository(db)
        # Re-use MovieService.get_movie() so the "movie not found" rule lives in one place.
        self.movie_service = MovieService(db)

    def list_favorites(self, limit: int, offset: int) -> MovieListResponse:
        movies = self.favorite_repository.list_favorite_movies(limit=limit, offset=offset)
        total = self.favorite_repository.count()
        return MovieListResponse(items=movies, total=total, limit=limit, offset=offset)

    def add_favorite(self, movie_id: int) -> Movie:
        """Mark a movie as favorite and return it (with isFavorite = true)."""
        movie = self.movie_service.get_movie(movie_id)  # 404 if the movie doesn't exist

        if movie.is_favorite:
            return movie  # Already a favorite: nothing to do.

        self.favorite_repository.add(movie)
        self.db.commit()
        return movie

    def remove_favorite(self, movie_id: int) -> None:
        """Remove a movie from favorites (no error if it wasn't a favorite)."""
        self.movie_service.get_movie(movie_id)  # 404 if the movie doesn't exist

        favorite = self.favorite_repository.get_by_movie_id(movie_id)
        if favorite is None:
            return  # Not a favorite: nothing to do.

        self.favorite_repository.delete(favorite)
        self.db.commit()
