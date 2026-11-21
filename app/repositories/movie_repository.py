"""
MovieRepository: all database queries for the `movies` table.

Rule of thumb for this project:
    - Repositories only TALK TO THE DATABASE (select / add / delete).
    - They never decide business rules, never commit, never raise HTTP errors.
    - The service layer decides WHEN to commit (one commit per use case).

Android analogy: a Room DAO (`MovieDao`).

SQLAlchemy 2.0 query style used here:
    statement = select(Movie).where(Movie.id == 5)   # build the query
    movie = self.db.scalars(statement).first()       # run it, get objects
"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Genre, Movie


class MovieRepository:
    def __init__(self, db: Session):
        # The session is passed in ("dependency injection"), so the same
        # repository works with the real database, a test database, or a script.
        self.db = db

    def get_by_id(self, movie_id: int) -> Movie | None:
        """Return the movie with this id, or None if it does not exist."""
        # db.get() looks up a row by primary key.
        return self.db.get(Movie, movie_id)

    def get_by_title_and_year(self, title: str, release_year: int) -> Movie | None:
        """Used to detect duplicates before inserting (case-insensitive title)."""
        statement = select(Movie).where(
            func.lower(Movie.title) == title.lower(),
            Movie.release_year == release_year,
        )
        return self.db.scalars(statement).first()

    def list_movies(self, search: str | None, limit: int, offset: int) -> list[Movie]:
        """
        Return one page of movies, best rated first.

        SQL produced (roughly):
            SELECT * FROM movies
            WHERE <search filter>
            ORDER BY rating DESC, id ASC
            LIMIT :limit OFFSET :offset
        """
        statement = select(Movie)
        statement = self._apply_search_filter(statement, search)
        # `id` as a second sort key makes the order stable when ratings are equal,
        # so the same movie never shows up on two different pages.
        statement = statement.order_by(Movie.rating.desc(), Movie.id.asc())
        statement = statement.limit(limit).offset(offset)
        return list(self.db.scalars(statement).all())

    def count_movies(self, search: str | None) -> int:
        """Total number of movies matching the search (ignores pagination)."""
        statement = select(func.count(Movie.id))
        statement = self._apply_search_filter(statement, search)
        return self.db.scalar(statement)

    def add(self, movie: Movie) -> Movie:
        """
        Stage a new movie for INSERT.

        flush() sends the INSERT to PostgreSQL now (inside the open transaction)
        so the movie gets its `id`, but nothing is permanent until the service
        calls commit().
        """
        self.db.add(movie)
        self.db.flush()
        return movie

    def delete(self, movie: Movie) -> None:
        """Stage the movie for DELETE (permanent after commit)."""
        self.db.delete(movie)

    # -- private helpers (leading underscore = "only used inside this class") --

    def _apply_search_filter(self, statement, search: str | None):
        """
        Same rule as the Android FakeMovieApiService: a movie matches when the
        search text appears in its TITLE or in any of its GENRE names,
        ignoring upper/lower case.

        ilike = case-insensitive LIKE. "%" means "any characters", so
        "%star%" matches "North Star Run".
        """
        if search is None or search == "":
            return statement

        pattern = f"%{search}%"
        title_matches = Movie.title.ilike(pattern)
        # .any(...) -> "at least one related genre matches" (an EXISTS subquery).
        genre_matches = Movie.genres.any(Genre.name.ilike(pattern))
        return statement.where(or_(title_matches, genre_matches))
