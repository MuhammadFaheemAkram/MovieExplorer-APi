"""
FavoriteRepository: database queries for the `favorites` table.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Favorite, Movie


class FavoriteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_movie_id(self, movie_id: int) -> Favorite | None:
        statement = select(Favorite).where(Favorite.movie_id == movie_id)
        return self.db.scalars(statement).first()

    def list_favorite_movies(self, limit: int, offset: int) -> list[Movie]:
        """
        Return favorited MOVIES, most recently favorited first.

        SQL produced (roughly):
            SELECT movies.* FROM movies
            JOIN favorites ON favorites.movie_id = movies.id
            ORDER BY favorites.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        statement = (
            select(Movie)
            .join(Favorite, Favorite.movie_id == Movie.id)
            .order_by(Favorite.created_at.desc(), Favorite.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.scalars(statement).all())

    def count(self) -> int:
        return self.db.scalar(select(func.count(Favorite.id)))

    def add(self, movie: Movie) -> Favorite:
        """
        Stage a new favorite for INSERT.

        Passing `movie=movie` (instead of `movie_id=movie.id`) also updates
        `movie.favorite` in memory, so `movie.is_favorite` is True right away.
        """
        favorite = Favorite(movie=movie)
        self.db.add(favorite)
        self.db.flush()
        return favorite

    def delete(self, favorite: Favorite) -> None:
        self.db.delete(favorite)
