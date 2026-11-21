"""Tests for the /api/v1/favorites endpoints."""

FAVORITES_URL = "/api/v1/favorites"
MOVIES_URL = "/api/v1/movies"


def test_add_favorite_marks_movie_as_favorite(client, make_movie):
    movie = make_movie()

    response = client.put(f"{FAVORITES_URL}/{movie['id']}")

    assert response.status_code == 200
    assert response.json()["isFavorite"] is True
    # The flag is also visible when the movie is loaded again.
    assert client.get(f"{MOVIES_URL}/{movie['id']}").json()["isFavorite"] is True


def test_add_favorite_twice_is_idempotent(client, make_movie):
    movie = make_movie()

    client.put(f"{FAVORITES_URL}/{movie['id']}")
    second_response = client.put(f"{FAVORITES_URL}/{movie['id']}")

    assert second_response.status_code == 200
    assert client.get(FAVORITES_URL).json()["total"] == 1


def test_list_favorites_newest_first(client, make_movie):
    first = make_movie(title="First")
    second = make_movie(title="Second")
    make_movie(title="Not a favorite")

    client.put(f"{FAVORITES_URL}/{first['id']}")
    client.put(f"{FAVORITES_URL}/{second['id']}")
    favorites = client.get(FAVORITES_URL).json()

    assert favorites["total"] == 2
    assert [movie["title"] for movie in favorites["items"]] == ["Second", "First"]


def test_remove_favorite(client, make_movie):
    movie = make_movie()
    client.put(f"{FAVORITES_URL}/{movie['id']}")

    response = client.delete(f"{FAVORITES_URL}/{movie['id']}")

    assert response.status_code == 204
    assert client.get(FAVORITES_URL).json()["total"] == 0
    assert client.get(f"{MOVIES_URL}/{movie['id']}").json()["isFavorite"] is False


def test_remove_non_favorite_is_not_an_error(client, make_movie):
    movie = make_movie()

    response = client.delete(f"{FAVORITES_URL}/{movie['id']}")

    assert response.status_code == 204


def test_favorite_missing_movie_returns_404(client):
    assert client.put(f"{FAVORITES_URL}/999").status_code == 404
    assert client.delete(f"{FAVORITES_URL}/999").status_code == 404


def test_deleting_movie_also_removes_its_favorite(client, make_movie):
    movie = make_movie()
    client.put(f"{FAVORITES_URL}/{movie['id']}")

    delete_response = client.delete(f"{MOVIES_URL}/{movie['id']}")

    assert delete_response.status_code == 204
    assert client.get(FAVORITES_URL).json()["total"] == 0
