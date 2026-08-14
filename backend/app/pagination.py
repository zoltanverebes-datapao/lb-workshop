"""Keyset pagination cursor encode/decode.

The cursor is the opaque encoding of the `(created_at, id)` pair of the last
row of a page. See `specs/S8.md` for the exact format and rationale.
"""

from __future__ import annotations

import base64
import binascii
import uuid
from datetime import datetime, timezone


class CursorError(ValueError):
    """Raised when a cursor string cannot be decoded into (created_at, id)."""


def encode_cursor(created_at: datetime, product_id: uuid.UUID) -> str:
    """Encode a (created_at, id) pair into an opaque base64url-no-padding cursor."""
    iso = created_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    raw = f"{iso}|{product_id}"
    encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).rstrip(b"=")
    return encoded.decode("ascii")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Decode a cursor string into a (created_at, id) pair.

    Raises `CursorError` if the cursor is not well-formed base64url of the
    `"<ISO-8601 created_at>|<id>"` shape.
    """
    padding = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(cursor + padding).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
        raise CursorError("cursor is not valid base64url") from exc

    parts = raw.split("|")
    if len(parts) != 2:
        raise CursorError("cursor does not decode to the expected shape")

    created_at_str, id_str = parts
    try:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CursorError("cursor timestamp is not valid ISO-8601") from exc

    try:
        product_id = uuid.UUID(id_str)
    except ValueError as exc:
        raise CursorError("cursor id is not a valid UUID") from exc

    return created_at, product_id
