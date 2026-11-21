"""
Custom errors and how they are turned into HTTP responses.

Why custom errors?
    Services contain business logic and should NOT know about HTTP
    (status codes, JSON, ...). So a service raises a plain Python error like
    `NotFoundError("Movie with id 5 was not found.")`, and the handlers below
    translate it into an HTTP response such as:

        404  {"detail": "Movie with id 5 was not found."}

    This keeps the service layer reusable (e.g. from scripts/seed_movies.py,
    which has no HTTP at all).

The `{"detail": ...}` shape is the same one FastAPI uses for its own errors,
so the client (Android app) only has to handle ONE error format.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


class AppError(Exception):
    """Base class for all errors our application raises on purpose."""

    # Subclasses override this with a more specific status code.
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    """The requested item does not exist -> HTTP 404."""

    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    """The request clashes with existing data (e.g. a duplicate) -> HTTP 409."""

    status_code = status.HTTP_409_CONFLICT


def register_exception_handlers(app: FastAPI) -> None:
    """Attach our error handlers to the FastAPI app (called from main.py)."""

    @app.exception_handler(AppError)
    def handle_app_error(request: Request, error: AppError) -> JSONResponse:
        # Works for NotFoundError, ConflictError and any future subclass,
        # because each one carries its own status_code.
        return JSONResponse(
            status_code=error.status_code,
            content={"detail": error.message},
        )

    @app.exception_handler(IntegrityError)
    def handle_integrity_error(request: Request, error: IntegrityError) -> JSONResponse:
        # Safety net: the database itself rejected the data (for example a
        # UNIQUE constraint). Our services check for duplicates first, but
        # two requests arriving at the exact same moment could both pass that
        # check - the database constraint is the final guard.
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "The request conflicts with existing data."},
        )
