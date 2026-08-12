#!/usr/bin/env bash
# The single verification entry point. Exit code is the verdict.
# Stages run cheapest-first so a type error does not cost a browser run.
set -euo pipefail

stage() { echo; echo "=== $1 ==="; }

# --- python lane -------------------------------------------------------------
stage "backend: lint"
(cd backend && uv run ruff check .)

stage "backend: types"
(cd backend && uv run mypy .)

stage "backend: tests"
(cd backend && uv run pytest -q)

# --- node lane ---------------------------------------------------------------
stage "frontend: types"
(cd frontend && npx tsc --noEmit)

stage "frontend: lint"
(cd frontend && npx eslint . --max-warnings=0)

stage "frontend: tests"
(cd frontend && npx vitest run --reporter=dot)

stage "frontend: build"
(cd frontend && npm run build)

# --- contract lane -----------------------------------------------------------
# Playwright owns the Postgres container (globalSetup) and both servers
# (webServer), including Yoyo migrations. Nothing to start here.
stage "contract"
npx playwright test --reporter=line

echo
echo "=== gate green ==="
