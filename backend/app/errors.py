"""House-shaped validation error handling.

FastAPI's default 422 body (`{"detail": [...]}`) does not match the house
shape (`docs/conventions.md`): `{"error": str, "field": str | None}`, one
field, the first failure only.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Location prefixes pydantic/FastAPI uses that are not themselves parameter
# names -- stripped so `field` is the bare query/path parameter name exactly
# as spelled in the URL, e.g. "limit" rather than "query.limit".
_LOCATION_PREFIXES = {"query", "body", "path", "header", "cookie"}


class ErrorResponse(BaseModel):
    """The house validation-error response shape."""

    error: str
    field: str | None = None


def _field_name(loc: Sequence[object]) -> str | None:
    """Extract the bare parameter name from a pydantic/FastAPI error location."""
    parts = [str(p) for p in loc if str(p) not in _LOCATION_PREFIXES]
    if parts:
        return parts[-1]
    return str(loc[-1]) if loc else None


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Return `{"error": <message>, "field": <name>}` for the first failure only."""
    assert isinstance(exc, RequestValidationError)
    errors = exc.errors()
    first: Mapping[str, object] = errors[0]
    loc = first.get("loc", ())
    field = _field_name(loc) if isinstance(loc, Sequence) else None
    message = str(first.get("msg", "Invalid request"))
    return JSONResponse(status_code=422, content={"error": message, "field": field})


def register_error_handlers(app: FastAPI) -> None:
    """Register the `RequestValidationError` handler on the app."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
