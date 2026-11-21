"""
Building blocks shared by all schemas.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """
    Base class for all request/response schemas.

    Python code uses snake_case (`poster_url`), but JSON APIs consumed by
    mobile/web apps usually use camelCase (`posterUrl`). This config converts
    automatically in both directions:

        Python attribute      JSON key
        ----------------      --------
        poster_url       <->  posterUrl
        is_favorite      <->  isFavorite

    Options:
      alias_generator=to_camel -> create the camelCase name for every field.
      populate_by_name=True    -> also accept snake_case input (handy in Python code/tests).
      from_attributes=True     -> allow building a schema directly from a
                                  SQLAlchemy object (reads movie.title, movie.rating, ...).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
