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
stage "web: types"
(cd web && npx tsc --noEmit)

stage "web: lint"
(cd web && npx eslint . --max-warnings=0)

stage "web: tests"
(cd web && npx vitest run --reporter=dot)

stage "web: build"
(cd web && npm run build)

# --- contract lane -----------------------------------------------------------
# Playwright owns the Postgres container (globalSetup) and both servers
# (webServer), including Yoyo migrations. Nothing to start here.
stage "contract"
npx playwright test --reporter=line

echo
echo "=== gate green ==="
