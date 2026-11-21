"""
The `genres` table.

Genres live in their own table (instead of a text column like "Sci-Fi|Thriller"
as the Android Room cache does) so that:
  - each genre name is stored once (no typos like "SciFi" vs "Sci-Fi"),
  - we can easily query "all movies of genre X",
  - we could later add extra genre info (icon, description, ...).
This is called database "normalization".
"""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.movie import movie_genres

if TYPE_CHECKING:
    from app.models.movie import Movie


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    # unique=True -> PostgreSQL refuses two genres with the same name.
    name: Mapped[str] = mapped_column(String(50), unique=True)

    # The other side of Movie.genres: genre.movies -> list of Movie objects.
    movies: Mapped[list["Movie"]] = relationship(
        secondary=movie_genres,
        back_populates="genres",
    )

    def __repr__(self) -> str:
        return f"<Genre id={self.id} name={self.name!r}>"
