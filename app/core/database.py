"""
Database connection setup.

Three important objects live here:

1. `engine`        - knows HOW to connect to PostgreSQL and keeps a pool of
                     open connections (opening a connection is slow, so they
                     are reused).
2. `SessionLocal`  - a factory that creates `Session` objects. A Session is a
                     "unit of work": you load/add/change objects through it and
                     then `commit()` everything in one transaction.
3. `get_db()`      - a FastAPI dependency that gives every HTTP request its own
                     Session and always closes it afterwards.

Android analogy: `engine` + `SessionLocal` ~ your Room `Database` builder,
and a Session ~ a single `withTransaction { }` block.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# echo=True prints every SQL statement to the console. Very useful while
# learning! Turn DEBUG off in .env if the output gets too noisy.
# pool_pre_ping=True checks a pooled connection is still alive before using it.
#
# CONNECTION POOL SIZE (a bug found by a load test, fixed 2026-11-17)
# ------------------------------------------------------------------
# SQLAlchemy's default pool is 5 connections + 10 overflow = 15, but FastAPI
# runs our `def` endpoints on 40 worker threads. With 200 requests at once:
#   1. 40 threads start requests; 15 get a connection, 25 wait for one.
#   2. A connection is given back when get_db() closes the session - but that
#      cleanup ALSO needs a free worker thread, and all 40 are busy waiting.
#   3. Deadlock until pool_timeout fires: only 24 of 200 requests succeeded.
# Rule: pool_size + max_overflow >= worker threads (40). After the fix, all
# 200 succeed. pool_timeout=10 makes any misconfiguration fail fast.
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=10,
)

# autoflush=False      -> SQL is only sent when WE decide (flush/commit), which is
#                         easier to reason about as a beginner.
# expire_on_commit=False -> objects keep their loaded values after commit(), so we
#                         can still return them from the API without re-loading.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for ONE request.

    This is a "generator" function (it uses `yield` instead of `return`):
      - code BEFORE `yield` runs when the request starts
      - the yielded `db` is handed to the endpoint
      - code AFTER `yield` (the `finally` block) runs when the request is done,
        even if an error happened. So the session is ALWAYS closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
