"""Tests for the /__test__ environment guard.

Both checks require a fresh Python process: the guard runs at module import
time (`app/main.py`), so it must be exercised via subprocess rather than by
importing (or re-importing) the already-loaded `app.main` module in this test
process.
"""

import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent

_DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/test_s2"


def test_seed_routes_404_when_app_env_unset() -> None:
    """/__test__/* is unreachable (404) when APP_ENV is not 'test'."""
    env = {**os.environ}
    env.pop("APP_ENV", None)
    env.setdefault("DATABASE_URL", _DEFAULT_DATABASE_URL)

    script = (
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n"
        "client = TestClient(app)\n"
        "r = client.post('/__test__/seed/products/three')\n"
        "print(r.status_code)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "404"


def test_refuses_to_start_with_non_localhost_database_url_under_app_env_test() -> None:
    """Importing app.main raises when APP_ENV=test and DATABASE_URL host isn't local."""
    env = {
        **os.environ,
        "APP_ENV": "test",
        "DATABASE_URL": "postgresql://postgres:postgres@example.com:5432/test_s2",
    }
    result = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "RuntimeError" in result.stderr
    assert "localhost" in result.stderr or "127.0.0.1" in result.stderr


def test_starts_fine_with_localhost_database_url_under_app_env_test() -> None:
    """The APP_ENV=test guard does not reject a genuinely local DATABASE_URL."""
    env = {
        **os.environ,
        "APP_ENV": "test",
        "DATABASE_URL": _DEFAULT_DATABASE_URL,
    }
    script = (
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n"
        "client = TestClient(app)\n"
        "r = client.post('/__test__/seed/products/no-such-fixture')\n"
        "print(r.status_code)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "404"
