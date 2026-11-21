"""
The `movies` table and the `movie_genres` link table.

Relationships in this file:
    Movie  <-- many-to-many -->  Genre      (through the movie_genres table)
    Movie  <-- one-to-one   -->  Favorite   (a movie is favorited at most once)
"""

# This import lets us write type hints that refer to classes defined in other
# files (Genre, Favorite) without importing them at runtime, which would cause
# a "circular import" (movie.py imports genre.py which imports movie.py ...).
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.favorite import Favorite
    from app.models.genre import Genre


# ---------------------------------------------------------------------------
# Link table for the many-to-many relationship between movies and genres.
#
#   movies            movie_genres             genres
#   ------            ------------             ------
#   id=1  ---------->  movie_id=1, genre_id=3  ---> id=3 "Sci-Fi"
#                      movie_id=1, genre_id=7  ---> id=7 "Thriller"
#
# It only holds two foreign keys, so we use a plain `Table` instead of a class.
# ondelete="CASCADE": when a movie (or genre) is deleted, PostgreSQL also
# deletes its rows in this table automatically.
# ---------------------------------------------------------------------------
movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)


class Movie(TimestampMixin, Base):
    """
    One row in the `movies` table.

    `Mapped[...]` declares the Python type, `mapped_column(...)` adds database
    details (length, index, constraints). `Mapped[str]` means NOT NULL;
    `Mapped[str | None]` would mean the column can be NULL.
    """

    __tablename__ = "movies"

    # Table-level rules that PostgreSQL enforces (a second line of defence
    # after Pydantic validation - protects data inserted by any other tool too).
    __table_args__ = (
        # The same title can exist twice only if released in different years
        # (think remakes), so (title, release_year) together must be unique.
        UniqueConstraint("title", "release_year"),
        CheckConstraint("rating >= 0 AND rating <= 10", name="rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)  # auto-increment 1, 2, 3...
    title: Mapped[str] = mapped_column(String(200), index=True)
    overview: Mapped[str] = mapped_column(Text)  # Text = unlimited length
    poster_url: Mapped[str] = mapped_column(String(500))
    backdrop_url: Mapped[str] = mapped_column(String(500))
    rating: Mapped[float]  # FLOAT column; no extra options needed
    release_year: Mapped[int]

    # --- Relationships (not real columns; SQLAlchemy loads them for us) -----

    # movie.genres -> list of Genre objects.
    # lazy="selectin": when we load a list of movies, SQLAlchemy loads ALL their
    # genres in ONE extra query (instead of one query per movie, the famous
    # "N+1 query problem").
    genres: Mapped[list["Genre"]] = relationship(
        secondary=movie_genres,
        back_populates="movies",
        order_by="Genre.name",
        lazy="selectin",
    )

    # movie.favorite -> a Favorite object, or None if not favorited.
    # cascade="all, delete-orphan": the favorite BELONGS to the movie, so
    #   deleting the movie deletes its favorite too. (Without this, SQLAlchemy
    #   would try to set favorites.movie_id = NULL, which the NOT NULL column
    #   rejects - a bug the test `test_deleting_movie_also_removes_its_favorite` caught.)
    # passive_deletes=True: if the favorite isn't loaded yet, don't load it
    #   just to delete it - PostgreSQL's ON DELETE CASCADE handles it.
    favorite: Mapped["Favorite | None"] = relationship(
        back_populates="movie",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    @property
    def is_favorite(self) -> bool:
        """
        Computed value (not stored in the database).
        Pydantic reads this when building the JSON response (`isFavorite`).
        """
        return self.favorite is not None

    def __repr__(self) -> str:
        # Controls how the object looks when printed - handy for debugging.
        return f"<Movie id={self.id} title={self.title!r}>"
