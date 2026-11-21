"""
Request and response schemas for movies.

Schemas (Pydantic models) describe the SHAPE of the JSON that goes in and out
of the API. They are NOT database tables - that's what app/models/ is for.

Android analogy:
    app/models/movie.py   (SQLAlchemy)  ~  MovieEntity (Room)
    app/schemas/movie.py  (Pydantic)    ~  MovieDto    (Retrofit/Gson)

Why separate classes for create / update / response?
    - MovieCreate:   what the client SENDS to create a movie (no id - the DB assigns it).
    - MovieUpdate:   every field optional, so the client can change just one field.
    - MovieResponse: what we SEND BACK (includes id, isFavorite, timestamps).
"""

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import CamelModel

# Must match String(50) on Genre.name in app/models/genre.py.
GENRE_NAME_MAX_LENGTH = 50


def clean_genre_names(names: list[str]) -> list[str]:
    """
    Normalize a list of genre names coming from the client:
      - remove spaces around each name ("  Drama " -> "Drama")
      - skip empty names
      - skip duplicates, ignoring upper/lower case ("drama" == "Drama")
      - reject names longer than the `genres.name` column (50 characters)

    Raising ValueError inside a Pydantic validator turns into a clean
    422 response. Without the length check, PostgreSQL would reject the
    INSERT and the client would get an unfriendly 500 error instead.
    """
    cleaned_names = []
    seen_lowercase = set()
    for name in names:
        name = name.strip()
        if name == "":
            continue
        if len(name) > GENRE_NAME_MAX_LENGTH:
            raise ValueError(f"each genre must have at most {GENRE_NAME_MAX_LENGTH} characters")
        if name.lower() in seen_lowercase:
            continue
        seen_lowercase.add(name.lower())
        cleaned_names.append(name)
    return cleaned_names


class MovieCreate(CamelModel):
    """
    Body of `POST /api/v1/movies`.

    Field(...) adds validation rules. If the client breaks a rule, FastAPI
    automatically answers 422 Unprocessable Entity with a helpful message -
    our code never even runs.
    """

    title: str = Field(min_length=1, max_length=200, examples=["Aurora Protocol"])
    overview: str = Field(min_length=1, max_length=5000)
    poster_url: str = Field(max_length=500, examples=["https://picsum.photos/seed/aurora/500/750"])
    backdrop_url: str = Field(max_length=500, examples=["https://picsum.photos/seed/aurora-bg/1200/675"])
    rating: float = Field(ge=0, le=10, examples=[8.2])  # ge = >=, le = <=
    release_year: int = Field(ge=1888, le=2100, examples=[2026])  # 1888: first film ever
    genres: list[str] = Field(default=[], max_length=10, examples=[["Sci-Fi", "Thriller"]])

    # A validator runs extra custom logic on one field.
    @field_validator("title", "overview")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if value == "":
            raise ValueError("must not be blank")
        return value

    @field_validator("genres")
    @classmethod
    def clean_genres(cls, value: list[str]) -> list[str]:
        return clean_genre_names(value)


class MovieUpdate(CamelModel):
    """
    Body of `PATCH /api/v1/movies/{id}`.

    Every field is optional (`| None = None`). Only the fields the client
    actually sends are updated; everything else stays the same.
    """

    title: str | None = Field(default=None, min_length=1, max_length=200)
    overview: str | None = Field(default=None, min_length=1, max_length=5000)
    poster_url: str | None = Field(default=None, max_length=500)
    backdrop_url: str | None = Field(default=None, max_length=500)
    rating: float | None = Field(default=None, ge=0, le=10)
    release_year: int | None = Field(default=None, ge=1888, le=2100)
    genres: list[str] | None = Field(default=None, max_length=10)

    @field_validator("genres")
    @classmethod
    def clean_genres(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return clean_genre_names(value)


class MovieResponse(CamelModel):
    """
    A movie as returned by the API. Example JSON:

        {
          "id": 1,
          "title": "Aurora Protocol",
          "overview": "...",
          "posterUrl": "https://...",
          "backdropUrl": "https://...",
          "rating": 8.2,
          "releaseYear": 2026,
          "genres": ["Sci-Fi", "Thriller"],
          "isFavorite": false,
          "createdAt": "2026-11-10T09:00:00Z",
          "updatedAt": "2026-11-10T09:00:00Z"
        }
    """

    id: int
    title: str
    overview: str
    poster_url: str
    backdrop_url: str
    rating: float
    release_year: int
    genres: list[str]
    is_favorite: bool  # comes from the Movie.is_favorite @property
    created_at: datetime
    updated_at: datetime

    @field_validator("genres", mode="before")
    @classmethod
    def genre_objects_to_names(cls, value: list) -> list[str]:
        """
        The database model gives us a list of Genre OBJECTS, but the JSON
        should contain plain names: ["Sci-Fi", "Thriller"].
        mode="before" means: run this BEFORE Pydantic checks the type.
        """
        names = []
        for genre in value:
            if isinstance(genre, str):
                names.append(genre)
            else:
                names.append(genre.name)
        return names


class MovieListResponse(CamelModel):
    """
    A page of movies. Example JSON:

        {"items": [...], "total": 42, "limit": 20, "offset": 0}

    Returning `total` lets the app know whether there are more pages to load
    (more items exist if offset + limit < total).
    """

    items: list[MovieResponse]
    total: int
    limit: int
    offset: int
