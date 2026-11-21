"""
GenreRepository: database queries for the `genres` table.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Genre


class GenreRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Genre | None:
        """Find a genre by name, ignoring upper/lower case ("drama" finds "Drama")."""
        statement = select(Genre).where(func.lower(Genre.name) == name.lower())
        return self.db.scalars(statement).first()

    def add(self, name: str) -> Genre:
        """Stage a new genre for INSERT and return it (with its new id)."""
        genre = Genre(name=name)
        self.db.add(genre)
        self.db.flush()
        return genre
