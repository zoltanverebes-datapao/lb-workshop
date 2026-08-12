"""Test configuration and shared fixtures."""

import os
import subprocess
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import psycopg
import pytest
import pytest_asyncio

# Default DATABASE_URL for local dev / CI
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/test_s2",
)

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"


def _run_init_db() -> None:
    """Apply all pending Yoyo migrations (idempotent)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "init_db.py")],
        env={**os.environ, "DATABASE_URL": DATABASE_URL},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"init_db.py failed:\n{result.stdout}\n{result.stderr}"
        )


def _run_truncate_db() -> None:
    """Truncate all user tables (preserves schema and _yoyo_migration)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "truncate_db.py")],
        env={**os.environ, "DATABASE_URL": DATABASE_URL},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"truncate_db.py failed:\n{result.stdout}\n{result.stderr}"
        )


def pytest_configure(config: pytest.Config) -> None:
    """Set DATABASE_URL default so db.py can be imported without raising."""
    os.environ.setdefault("DATABASE_URL", DATABASE_URL)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Run init_db once at the start of the test session.

    If Postgres is not reachable, this is a warning only — tests that do not
    require a database connection will still pass.
    """
    try:
        _run_init_db()
    except Exception as exc:
        # Don't abort the whole session; tests that need DB will fail naturally
        print(f"\nWARNING: init_db skipped — {exc}", file=sys.stderr)


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    """Truncate tables after each test to ensure isolation."""
    try:
        _run_truncate_db()
    except Exception:
        # Ignore truncation errors (Postgres may not be running)
        pass


AsyncConn = psycopg.AsyncConnection[psycopg.rows.TupleRow]


@pytest_asyncio.fixture
async def db_conn() -> AsyncGenerator[AsyncConn, None]:
    """Yield an async psycopg connection for tests that need direct DB access."""
    async with await psycopg.AsyncConnection.connect(DATABASE_URL) as conn:
        yield conn
