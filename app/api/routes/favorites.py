"""
Favorite endpoints.

    GET    /favorites             list favorite movies (newest favorite first)
    PUT    /favorites/{movie_id}  add a movie to favorites
    DELETE /favorites/{movie_id}  remove a movie from favorites

Why PUT and DELETE (instead of one "toggle" endpoint)?
    A toggle is NOT safe to retry: if the network drops and the app sends it
    twice, the movie flips back. PUT ("make it a favorite") and DELETE
    ("make it NOT a favorite") give the same result no matter how many times
    they are sent (they are "idempotent"). The Android app's
    `toggleFavorite(movie)` just picks one of them based on `movie.isFavorite`.
"""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import FavoriteServiceDep
from app.schemas import MovieListResponse, MovieResponse

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("", response_model=MovieListResponse)
def list_favorites(
    service: FavoriteServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List favorite movies. Replaces the Android Room `observeFavoriteMovies()` query."""
    return service.list_favorites(limit=limit, offset=offset)


@router.put("/{movie_id}", response_model=MovieResponse)
def add_favorite(movie_id: int, service: FavoriteServiceDep):
    """Add a movie to favorites and return it with `isFavorite: true`."""
    return service.add_favorite(movie_id)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(movie_id: int, service: FavoriteServiceDep):
    """Remove a movie from favorites. Returns **204 No Content**."""
    service.remove_favorite(movie_id)
