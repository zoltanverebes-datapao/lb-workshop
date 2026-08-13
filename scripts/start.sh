#!/usr/bin/env bash
set -e

if [ -z "${DATABASE_URL}" ]; then
  DATABASE_URL="postgresql://${PGUSER}@${PGHOST}:${PGPORT}/${PGDATABASE}?sslmode=${PGSSLMODE}"
fi
export DATABASE_URL

cd frontend && npm install
npm run build

cd ../backend
uv sync

exec uv run uvicorn app.main:app --host 0.0.0.0 --port "$DATABRICKS_APP_PORT"
