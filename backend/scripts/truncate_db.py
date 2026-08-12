"""Truncate all user-created tables in the database (for test isolation).

Preserves the schema (table definitions) and the _yoyo_migration tracking table.
This script is idempotent — safe to run multiple times.
Reads DATABASE_URL from the environment.
"""

import os
import sys

import psycopg


def main() -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/app",
    )

    print("Truncating user tables ...")
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            # Find all user-created tables, excluding Yoyo migration tracking tables
            cur.execute(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename NOT LIKE '_yoyo%'
                  AND tablename NOT LIKE 'yoyo%'
                ORDER BY tablename
                """
            )
            tables = [row[0] for row in cur.fetchall()]

            if tables:
                table_list = ", ".join(f'"{t}"' for t in tables)
                print(f"Truncating: {table_list}")
                cur.execute(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE")
                conn.commit()
                print("Done.")
            else:
                print("No user tables found — nothing to truncate.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
