"""Initialize the database schema by applying all pending Yoyo migrations.

This script is idempotent — running it multiple times is safe.
It reads DATABASE_URL from the environment (defaults to a localhost URL for dev).
"""

import os
import sys
from pathlib import Path

from yoyo import get_backend, read_migrations


def main() -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/app",
    )

    # Convert postgresql:// to postgresql+psycopg:// for Yoyo's psycopg 3 backend
    yoyo_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    migrations_path = str(Path(__file__).parent.parent / "migrations")

    print(f"Applying migrations from {migrations_path} ...")
    backend = get_backend(yoyo_url)
    migrations = read_migrations(migrations_path)
    with backend.lock():
        to_apply = backend.to_apply(migrations)
        if to_apply:
            print(f"Applying {len(list(to_apply))} migration(s).")
            to_apply = backend.to_apply(migrations)
            backend.apply_migrations(to_apply)
        else:
            print("No pending migrations — database is up to date.")
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
