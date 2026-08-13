"""Async PostgreSQL connection pool and FastAPI dependency."""

import os
from collections.abc import AsyncGenerator

import psycopg
import psycopg.rows
from psycopg.abc import ConnParam
from psycopg_pool import AsyncConnectionPool

_database_url = os.environ.get("DATABASE_URL")
_pghost = os.environ.get("PGHOST")

if _database_url:
    # Path A -- Local/test: use DATABASE_URL directly, no Databricks SDK.
    pool: AsyncConnectionPool[psycopg.AsyncConnection[psycopg.rows.TupleRow]] = (
        AsyncConnectionPool(
            conninfo=_database_url,
            open=False,
        )
    )

    def get_yoyo_url() -> str:
        """Return a Yoyo-compatible synchronous connection URL (Path A)."""
        assert _database_url is not None
        return _database_url.replace("postgresql://", "postgresql+psycopg://", 1)

elif _pghost:
    # Path B -- Databricks Lakebase: fetch fresh OAuth token per connection.
    _pgdatabase = os.environ["PGDATABASE"]
    _pguser = os.environ["PGUSER"]
    _pgport = os.environ.get("PGPORT", "5432")
    _pgsslmode = os.environ.get("PGSSLMODE", "require")
    _endpoint_name = os.environ["ENDPOINT_NAME"]

    _conninfo = (
        f"dbname={_pgdatabase} user={_pguser} host={_pghost} "
        f"port={_pgport} sslmode={_pgsslmode}"
    )

    class OAuthAsyncConnection(
        psycopg.AsyncConnection[psycopg.rows.TupleRow]
    ):
        """AsyncConnection subclass that injects a fresh Databricks OAuth token."""

        @classmethod
        async def connect(
            cls,
            conninfo: str = "",
            *,
            autocommit: bool = False,
            prepare_threshold: int | None = 5,
            context: psycopg.abc.AdaptContext | None = None,
            row_factory: psycopg.rows.AsyncRowFactory[psycopg.rows.TupleRow]
            | None = None,
            cursor_factory: type[
                psycopg.AsyncCursor[psycopg.rows.TupleRow]
            ]
            | None = None,
            **kwargs: ConnParam,
        ) -> "OAuthAsyncConnection":
            from databricks.sdk import WorkspaceClient

            w = WorkspaceClient()
            credential = w.postgres.generate_database_credential(
                endpoint=_endpoint_name
            )
            kwargs["password"] = credential.token
            return await super().connect(
                conninfo,
                autocommit=autocommit,
                prepare_threshold=prepare_threshold,
                context=context,
                row_factory=row_factory,
                cursor_factory=cursor_factory,
                **kwargs,
            )

    pool = AsyncConnectionPool(
        conninfo=_conninfo,
        connection_class=OAuthAsyncConnection,
        open=False,
    )

    def get_yoyo_url() -> str:
        """Return a Yoyo-compatible synchronous connection URL (Path B)."""
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient()
        credential = w.postgres.generate_database_credential(
            endpoint=_endpoint_name
        )
        token = credential.token
        return (
            f"postgresql+psycopg://{_pguser}:{token}@{_pghost}:{_pgport}"
            f"/{_pgdatabase}?sslmode={_pgsslmode}"
        )

else:
    # Path C -- Neither DATABASE_URL nor PGHOST is set.
    raise RuntimeError(
        "No database configuration found. Set either DATABASE_URL (local/test) "
        "or PGHOST (Databricks Lakebase). Neither DATABASE_URL nor PGHOST is set."
    )


AsyncConn = psycopg.AsyncConnection[psycopg.rows.TupleRow]


async def get_conn() -> AsyncGenerator[AsyncConn, None]:
    """FastAPI dependency that yields an async database connection."""
    async with pool.connection() as conn:
        yield conn
