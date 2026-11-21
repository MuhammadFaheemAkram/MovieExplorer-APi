"""
Shared base class for every database model (table).

Every model class inherits from `Base`. SQLAlchemy uses it to collect all
tables into `Base.metadata`, which Alembic reads to generate migrations.
"""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naming convention for constraints (primary keys, foreign keys, unique, ...).
# Without it, PostgreSQL invents random names, which makes later migrations
# (e.g. "drop this unique constraint") painful. With it, names are predictable:
#     uq_genres_name, fk_favorites_movie_id_movies, ...
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Parent class of all models. Android analogy: Room's @Entity classes."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    """
    Adds `created_at` and `updated_at` columns to any model that inherits it.

    A "mixin" is a small class you inherit from just to reuse some fields,
    so you don't have to copy-paste them into every model.

    server_default=func.now() -> PostgreSQL fills in the current time itself.
    onupdate=func.now()       -> SQLAlchemy sets a new time on every UPDATE.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
