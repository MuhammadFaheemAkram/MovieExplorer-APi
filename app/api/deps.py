"""
FastAPI dependencies ("dependency injection").

A dependency is a function FastAPI calls FOR you before running an endpoint.
Its return value is passed into the endpoint as a parameter.

Chain for every request:
    get_db()  ->  Session  ->  get_movie_service(db)  ->  MovieService(db)  ->  endpoint

Android analogy: Hilt modules (`@Provides fun provideMovieRepository(...)`).

`Annotated[MovieService, Depends(get_movie_service)]` means:
    "the type is MovieService, and FastAPI should build it by calling
     get_movie_service()". Giving it a short name (MovieServiceDep) keeps
     endpoint signatures readable.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import FavoriteService, MovieService

# "A SQLAlchemy Session, created by get_db()".
DbSession = Annotated[Session, Depends(get_db)]


def get_movie_service(db: DbSession) -> MovieService:
    return MovieService(db)


def get_favorite_service(db: DbSession) -> FavoriteService:
    return FavoriteService(db)


MovieServiceDep = Annotated[MovieService, Depends(get_movie_service)]
FavoriteServiceDep = Annotated[FavoriteService, Depends(get_favorite_service)]
