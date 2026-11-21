"""
Tests for the /api/v1/movies endpoints.

Run all tests:        pytest
Run just this file:   pytest tests/test_movies.py
Verbose output:       pytest -v

Every test follows the same pattern ("Arrange - Act - Assert"):
    1. Arrange: create the data the test needs.
    2. Act:     call the endpoint.
    3. Assert:  check the status code and the JSON.
"""

MOVIES_URL = "/api/v1/movies"


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


# ------------------------------------------------------------------ CREATE


def test_create_movie_returns_201_and_camel_case_json(client, make_movie):
    movie = make_movie()

    assert movie["id"] == 1
    assert movie["title"] == "Aurora Protocol"
    assert movie["posterUrl"] == "https://picsum.photos/seed/a/500/750"
    assert movie["releaseYear"] == 2026
    assert movie["genres"] == ["Sci-Fi", "Thriller"]
    assert movie["isFavorite"] is False
    assert "createdAt" in movie


def test_create_movie_reuses_existing_genres_and_cleans_names(client, make_movie):
    make_movie(title="First", genres=["Drama"])
    second = make_movie(title="Second", genres=["  drama ", "Comedy", "COMEDY"])

    # " drama " matched the existing "Drama"; the duplicate "COMEDY" was dropped.
    assert second["genres"] == ["Comedy", "Drama"]


def test_create_duplicate_movie_returns_409(client, make_movie):
    make_movie(title="Aurora Protocol", releaseYear=2026)

    response = client.post(
        MOVIES_URL,
        json={
            "title": "aurora protocol",  # different case, still a duplicate
            "overview": "Again",
            "posterUrl": "x",
            "backdropUrl": "y",
            "rating": 5,
            "releaseYear": 2026,
        },
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_same_title_different_year_is_allowed(client, make_movie):
    make_movie(title="Remake", releaseYear=1990)
    make_movie(title="Remake", releaseYear=2025)  # no error = pass


def test_create_movie_with_invalid_data_returns_422(client):
    response = client.post(
        MOVIES_URL,
        json={
            "title": "",  # too short
            "overview": "ok",
            "posterUrl": "x",
            "backdropUrl": "y",
            "rating": 11,  # above 10
            "releaseYear": 2026,
        },
    )

    assert response.status_code == 422
    # FastAPI lists every invalid field in "detail".
    invalid_fields = []
    for error in response.json()["detail"]:
        invalid_fields.append(error["loc"][-1])
    assert "title" in invalid_fields
    assert "rating" in invalid_fields


def test_too_long_genre_returns_422_not_500(client, make_movie):
    # Regression test: genres.name is VARCHAR(50). Before the schema checked the
    # length, PostgreSQL rejected the INSERT and the API crashed with a 500.
    response = client.post(
        MOVIES_URL,
        json={
            "title": "Long Genre",
            "overview": "ok",
            "posterUrl": "x",
            "backdropUrl": "y",
            "rating": 5,
            "releaseYear": 2026,
            "genres": ["G" * 51],
        },
    )

    assert response.status_code == 422


# -------------------------------------------------------------------- READ


def test_get_movie_by_id(client, make_movie):
    created = make_movie()

    response = client.get(f"{MOVIES_URL}/{created['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == "Aurora Protocol"


def test_get_missing_movie_returns_404(client):
    response = client.get(f"{MOVIES_URL}/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Movie with id 999 was not found."}


def test_list_movies_is_sorted_by_rating_and_paginated(client, make_movie):
    make_movie(title="Low", rating=5.0)
    make_movie(title="High", rating=9.0)
    make_movie(title="Mid", rating=7.0)

    first_page = client.get(MOVIES_URL, params={"limit": 2, "offset": 0}).json()
    second_page = client.get(MOVIES_URL, params={"limit": 2, "offset": 2}).json()

    assert first_page["total"] == 3
    assert [movie["title"] for movie in first_page["items"]] == ["High", "Mid"]
    assert [movie["title"] for movie in second_page["items"]] == ["Low"]


def test_search_matches_title_or_genre_case_insensitive(client, make_movie):
    make_movie(title="North Star Run", genres=["Action"])
    make_movie(title="Paper Moons", genres=["Fantasy"])
    make_movie(title="Orbit Cafe", genres=["Sci-Fi", "Comedy"])

    by_title = client.get(MOVIES_URL, params={"search": "STAR"}).json()
    by_genre = client.get(MOVIES_URL, params={"search": "comedy"}).json()
    no_match = client.get(MOVIES_URL, params={"search": "zzz"}).json()

    assert [movie["title"] for movie in by_title["items"]] == ["North Star Run"]
    assert [movie["title"] for movie in by_genre["items"]] == ["Orbit Cafe"]
    assert no_match == {"items": [], "total": 0, "limit": 20, "offset": 0}


# ------------------------------------------------------------------ UPDATE


def test_patch_updates_only_sent_fields(client, make_movie):
    created = make_movie(rating=7.0, genres=["Drama"])

    response = client.patch(
        f"{MOVIES_URL}/{created['id']}",
        json={"rating": 9.5, "genres": ["Action"]},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["rating"] == 9.5
    assert updated["genres"] == ["Action"]
    assert updated["title"] == created["title"]  # unchanged


def test_patch_to_duplicate_title_returns_409(client, make_movie):
    make_movie(title="Taken", releaseYear=2020)
    other = make_movie(title="Free", releaseYear=2020)

    response = client.patch(f"{MOVIES_URL}/{other['id']}", json={"title": "Taken"})

    assert response.status_code == 409


# ------------------------------------------------------------------ DELETE


def test_delete_movie(client, make_movie):
    created = make_movie()

    delete_response = client.delete(f"{MOVIES_URL}/{created['id']}")
    get_response = client.get(f"{MOVIES_URL}/{created['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
