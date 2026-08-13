#!/usr/bin/env bash
set -e

cd frontend && npm install
npm run build

cd ../backend
uv sync

exec uv run uvicorn app.main:app --host 0.0.0.0 --port "$DATABRICKS_APP_PORT"
