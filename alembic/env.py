"""
Alembic environment script - runs every time you use an `alembic` command.

What is Alembic?
    "Git for your database schema". Each change to the tables (new table,
    new column, ...) is saved as a small Python file in alembic/versions/.
    Running `alembic upgrade head` applies all files that the database has
    not seen yet, in order. Alembic remembers what was applied in a table
    called `alembic_version`.

    Android analogy: Room `Migration(1, 2) { ... }` objects - but generated
    for you by comparing your models with the real database.

Only two things were customized in this file (search for "CUSTOMIZED"):
    1. The database URL comes from our app settings (.env), not alembic.ini.
    2. `target_metadata` points at our models so `--autogenerate` can detect changes.
"""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# CUSTOMIZED: import our settings and ALL models (via app.models).
from app.core.config import settings
from app.models import Base

# Alembic's config object (values from alembic.ini).
config = context.config

# Set up logging as described in alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# CUSTOMIZED: the "desired" schema. Autogenerate compares this with the real
# database and writes the difference into a new migration file.
target_metadata = Base.metadata

# CUSTOMIZED: single source of truth for the connection string.
DATABASE_URL = settings.database_url


def run_migrations_offline() -> None:
    """
    'Offline' mode: `alembic upgrade head --sql` prints the SQL instead of
    running it. Useful if a DBA must review/run the SQL by hand.
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """'Online' mode (the normal case): connect to the database and apply changes."""
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # also detect column TYPE changes (e.g. String(100) -> String(200))
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
