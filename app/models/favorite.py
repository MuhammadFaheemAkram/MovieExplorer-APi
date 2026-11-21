"""
The `favorites` table.

Why a separate table instead of an `is_favorite` column on `movies`?
    Because "favorite" is not a property of a movie - it is a relationship
    between a USER and a movie. We have no users yet (no authentication), so
    there is one global favorites list. When authentication is added later,
    we only need to add a `user_id` column here and make (user_id, movie_id)
    unique - the movies table does not change at all.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.movie import Movie


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ForeignKey -> must point to an existing movie id.
    # unique=True -> the same movie cannot be favorited twice.
    # ondelete="CASCADE" -> deleting a movie also deletes its favorite row.
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        unique=True,
    )

    # When the movie was added to favorites (used to sort the favorites list).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # favorite.movie -> the Movie object this row points to.
    movie: Mapped["Movie"] = relationship(back_populates="favorite")

    def __repr__(self) -> str:
        return f"<Favorite id={self.id} movie_id={self.movie_id}>"
