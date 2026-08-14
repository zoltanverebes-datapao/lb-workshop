"""Unit tests for app.pagination: cursor encode/decode."""

import uuid
from datetime import datetime, timezone

import pytest

from app.pagination import CursorError, decode_cursor, encode_cursor


def test_round_trip() -> None:
    """Encoding then decoding returns the original (created_at, id)."""
    created_at = datetime(2026, 1, 1, 0, 3, tzinfo=timezone.utc)
    product_id = uuid.uuid4()

    cursor = encode_cursor(created_at, product_id)
    decoded_created_at, decoded_id = decode_cursor(cursor)

    assert decoded_created_at == created_at
    assert decoded_id == product_id


def test_encoded_cursor_has_no_padding() -> None:
    """Cursor is base64url, no `=` padding characters."""
    cursor = encode_cursor(datetime(2026, 1, 1, tzinfo=timezone.utc), uuid.uuid4())
    assert "=" not in cursor


def test_decode_rejects_non_base64() -> None:
    """A string that is not valid base64url raises CursorError."""
    with pytest.raises(CursorError):
        decode_cursor("not-a-cursor")


def test_decode_rejects_base64_without_separator() -> None:
    """Valid base64url that decodes to a string without the '|' separator."""
    with pytest.raises(CursorError):
        decode_cursor("Zm9v")  # "foo" -- valid base64url, wrong shape


def test_decode_rejects_bad_uuid() -> None:
    """Well-shaped cursor with an invalid UUID component raises CursorError."""
    import base64

    raw = "2026-01-01T00:00:00Z|not-a-uuid"
    bad_cursor = base64.urlsafe_b64encode(raw.encode()).rstrip(b"=").decode()
    with pytest.raises(CursorError):
        decode_cursor(bad_cursor)


def test_decode_rejects_bad_timestamp() -> None:
    """Well-shaped cursor with an invalid timestamp component raises CursorError."""
    import base64

    raw = f"not-a-timestamp|{uuid.uuid4()}"
    bad_cursor = base64.urlsafe_b64encode(raw.encode()).rstrip(b"=").decode()
    with pytest.raises(CursorError):
        decode_cursor(bad_cursor)
