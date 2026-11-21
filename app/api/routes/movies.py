"""
Movie endpoints (the "controller" / HTTP layer).

Each function below is an endpoint. Its job is ONLY to:
    1. receive the HTTP input (path params, query params, JSON body) - FastAPI
       parses and validates these automatically from the type hints,
    2. call the service,
    3. return the result - FastAPI converts it to JSON using `response_model`.

No SQL and no business rules here. Android analogy: a ViewModel - it takes
input, delegates to use cases, and exposes the result.

Endpoints (all under /api/v1):
    GET    /movies            list + search, paginated
    GET    /movies/{movie_id} one movie
    POST   /movies            create
    PATCH  /movies/{movie_id} partial update
    DELETE /movies/{movie_id} delete
"""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import MovieServiceDep
from app.schemas import MovieCreate, MovieListResponse, MovieResponse, MovieUpdate

# prefix: every route below starts with /movies.
# tags:   groups these endpoints together in the Swagger docs at /docs.
router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("", response_model=MovieListResponse)
def list_movies(
    service: MovieServiceDep,
    # Query(...) = value comes from the URL: /movies?search=star&limit=10&offset=0
    search: Annotated[
        str | None,
        Query(max_length=100, description="Match against movie title or genre name (case-insensitive)."),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size (max 100).")] = 20,
    offset: Annotated[int, Query(ge=0, description="How many items to skip.")] = 0,
):
    """
    List movies, best rated first. Replaces the Android app's
    `getTrendingMovies()` and `searchMovies(query)`.
    """
    return service.list_movies(search=search, limit=limit, offset=offset)


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, service: MovieServiceDep):
    """
    Get one movie by id. `movie_id` comes from the URL path (/movies/3) and
    FastAPI checks it is an integer (otherwise: 422).
    Replaces the Android app's `getMovieDetails(id)`.
    """
    return service.get_movie(movie_id)


@router.post("", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
def create_movie(movie_in: MovieCreate, service: MovieServiceDep):
    """
    Create a movie. Because `movie_in` is a Pydantic model, FastAPI reads it
    from the JSON request body and validates it before this code runs.

    Returns **201 Created**, or **409 Conflict** if the same title + year exists.
    """
    return service.create_movie(movie_in)


@router.patch("/{movie_id}", response_model=MovieResponse)
def update_movie(movie_id: int, movie_in: MovieUpdate, service: MovieServiceDep):
    """Update only the fields present in the body, e.g. `{"rating": 9.0}`."""
    return service.update_movie(movie_id, movie_in)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, service: MovieServiceDep):
    """Delete a movie. Returns **204 No Content** (success, empty body)."""
    service.delete_movie(movie_id)
