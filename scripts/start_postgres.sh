#!/usr/bin/env bash
# Idempotent script to start the local Postgres container and ensure
# the test_s2 database exists.
#
# Usage: bash scripts/start_postgres.sh

set -euo pipefail

CONTAINER_NAME="lakebase-postgres"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if the container is already running
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container '${CONTAINER_NAME}' is already running. Nothing to do."
else
    echo "Starting Postgres container via docker-compose ..."
    docker-compose -f "${ROOT_DIR}/docker-compose.yml" up -d

    echo "Waiting for Postgres to be ready on localhost:5432 ..."
    TIMEOUT=30
    ELAPSED=0
    until docker exec "${CONTAINER_NAME}" pg_isready -U postgres -q 2>/dev/null; do
        if [ "${ELAPSED}" -ge "${TIMEOUT}" ]; then
            echo "ERROR: Postgres did not become ready within ${TIMEOUT} seconds." >&2
            exit 1
        fi
        sleep 1
        ELAPSED=$((ELAPSED + 1))
    done
    echo "Postgres is ready."
fi

# Create test_s2 database if it doesn't exist
if docker exec "${CONTAINER_NAME}" psql -U postgres -lqt | cut -d '|' -f1 | grep -qw "test_s2"; then
    echo "Database 'test_s2' already exists."
else
    echo "Creating database 'test_s2' ..."
    docker exec "${CONTAINER_NAME}" psql -U postgres -c "CREATE DATABASE test_s2;"
    echo "Database 'test_s2' created."
fi
