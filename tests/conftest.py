"""
Shared test setup ("fixtures") for pytest.

A fixture is a function that prepares something a test needs. A test asks for
it simply by using its name as a parameter:

    def test_something(client):   # pytest runs the `client` fixture first
        client.get("/health")

Strategy used here (simple and easy to follow):
    - Tests use a SEPARATE database (TEST_DATABASE_URL), never your real data.
    - Before all tests: create the tables from the models.
    - After EACH test: empty all tables, so every test starts from a clean state.
    - The app's `get_db` dependency is swapped for one that uses the test database.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models import Base

if settings.test_database_url is None:
    raise RuntimeError("Set TEST_DATABASE_URL in .env before running the tests.")

test_engine = create_engine(settings.test_database_url)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """
    Runs ONCE for the whole test run (scope="session").
    autouse=True -> applies automatically, no test needs to ask for it.

    For tests we build tables straight from the models with create_all();
    the real database uses Alembic migrations instead.
    """
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield  # <- all tests run here
    Base.metadata.drop_all(test_engine)


@pytest.fixture(autouse=True)
def clean_tables():
    """Runs after EVERY test: wipe all rows and reset ids back to 1."""
    yield
    with test_engine.begin() as connection:
        connection.execute(
            text("TRUNCATE movie_genres, favorites, movies, genres RESTART IDENTITY CASCADE")
        )


def override_get_db():
    """Same as app.core.database.get_db, but connected to the TEST database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """
    A fake HTTP client that calls the app directly in memory (no real server).
    Usage: response = client.get("/api/v1/movies")
    """
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_movie(client):
    """
    Helper fixture that creates a movie through the API and returns its JSON.
    Pass keyword arguments to override any field:
        movie = make_movie(title="Other", rating=5.0)
    """

    def _make_movie(**overrides):
        payload = {
            "title": "Aurora Protocol",
            "overview": "A rescue pilot discovers a hidden signal.",
            "posterUrl": "https://picsum.photos/seed/a/500/750",
            "backdropUrl": "https://picsum.photos/seed/b/1200/675",
            "rating": 8.2,
            "releaseYear": 2026,
            "genres": ["Sci-Fi", "Thriller"],
        }
        payload.update(overrides)
        response = client.post("/api/v1/movies", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make_movie
