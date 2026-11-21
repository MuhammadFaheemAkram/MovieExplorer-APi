"""
MovieService: business logic for movies.

Responsibilities of a service:
    - Enforce business rules ("no duplicate movies", "genres are reused").
    - Coordinate one or more repositories.
    - Decide when the transaction is committed.
    - Raise our own errors (NotFoundError, ConflictError) - never HTTP errors.

Android analogy: your UseCases (GetMovieDetailsUseCase, SearchMoviesUseCase, ...)
grouped into one class per feature.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models import Genre, Movie
from app.repositories import GenreRepository, MovieRepository
from app.schemas import MovieCreate, MovieListResponse, MovieUpdate


class MovieService:
    def __init__(self, db: Session):
        self.db = db
        self.movie_repository = MovieRepository(db)
        self.genre_repository = GenreRepository(db)

    # ------------------------------------------------------------------ READ

    def list_movies(self, search: str | None, limit: int, offset: int) -> MovieListResponse:
        """List movies (optionally filtered by a search text), one page at a time."""
        if search is not None:
            search = search.strip()

        movies = self.movie_repository.list_movies(search=search, limit=limit, offset=offset)
        total = self.movie_repository.count_movies(search=search)

        # Pydantic converts each Movie database object into a MovieResponse
        # (possible thanks to from_attributes=True in CamelModel).
        return MovieListResponse(items=movies, total=total, limit=limit, offset=offset)

    def get_movie(self, movie_id: int) -> Movie:
        """Return one movie or raise NotFoundError (-> HTTP 404)."""
        movie = self.movie_repository.get_by_id(movie_id)
        if movie is None:
            raise NotFoundError(f"Movie with id {movie_id} was not found.")
        return movie

    # ----------------------------------------------------------------- WRITE

    def create_movie(self, data: MovieCreate) -> Movie:
        """Create a new movie. Raises ConflictError if it already exists."""
        self._ensure_not_duplicate(data.title, data.release_year)

        movie = Movie(
            title=data.title,
            overview=data.overview,
            poster_url=data.poster_url,
            backdrop_url=data.backdrop_url,
            rating=data.rating,
            release_year=data.release_year,
        )
        movie.genres = self._get_or_create_genres(data.genres)

        self.movie_repository.add(movie)
        self.db.commit()  # Make everything permanent in ONE transaction.
        self.db.refresh(movie)  # Reload values PostgreSQL generated (created_at, ...).
        return movie

    def update_movie(self, movie_id: int, data: MovieUpdate) -> Movie:
        """Partially update a movie: only the fields the client sent are changed."""
        movie = self.get_movie(movie_id)

        # exclude_unset=True -> only fields that were present in the JSON body.
        # Example: body {"rating": 9.1} gives {"rating": 9.1}, nothing else.
        changes = data.model_dump(exclude_unset=True)

        # If title or year changes, the new combination must still be unique.
        new_title = changes.get("title", movie.title)
        new_year = changes.get("release_year", movie.release_year)
        if new_title.lower() != movie.title.lower() or new_year != movie.release_year:
            self._ensure_not_duplicate(new_title, new_year)

        # Genres need special handling (names -> Genre objects), so take them out.
        if "genres" in changes:
            genre_names = changes.pop("genres")
            if genre_names is not None:
                movie.genres = self._get_or_create_genres(genre_names)

        # Copy every remaining changed value onto the movie object.
        # setattr(movie, "rating", 9.1) is the same as writing movie.rating = 9.1
        for field_name, new_value in changes.items():
            if new_value is None:
                continue  # Columns are NOT NULL, so ignore explicit nulls.
            setattr(movie, field_name, new_value)

        self.db.commit()
        self.db.refresh(movie)
        return movie

    def delete_movie(self, movie_id: int) -> None:
        """Delete a movie. Its genre links and favorite are removed automatically."""
        movie = self.get_movie(movie_id)
        self.movie_repository.delete(movie)
        self.db.commit()

    # --------------------------------------------------------------- HELPERS

    def _ensure_not_duplicate(self, title: str, release_year: int) -> None:
        existing_movie = self.movie_repository.get_by_title_and_year(title, release_year)
        if existing_movie is not None:
            raise ConflictError(
                f"A movie titled '{title}' from {release_year} already exists "
                f"(id {existing_movie.id})."
            )

    def _get_or_create_genres(self, genre_names: list[str]) -> list[Genre]:
        """
        Turn ["Sci-Fi", "Thriller"] into Genre objects.
        Existing genres are reused; unknown ones are created.
        """
        genres = []
        for name in genre_names:
            genre = self.genre_repository.get_by_name(name)
            if genre is None:
                genre = self.genre_repository.add(name)
            genres.append(genre)
        return genres
