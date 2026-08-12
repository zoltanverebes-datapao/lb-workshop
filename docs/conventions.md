# Conventions

House rules inherited by every spec, every agent, every round. Specs do not
restate anything here.

Grow this file from failures, not from imagination. When a round FAILs because
two agents assumed different things, the resolution becomes a line here before
the next item starts.

## Stack

- Backend: FastAPI, Python 3.12, `uv`, psycopg 3 (async, raw SQL), Yoyo migrations, pytest
- Frontend: React 19, Vite, TypeScript strict, vitest, React Testing Library
- Database: PostgreSQL 16
- Contract tests: Playwright

## Ports

| | dev | test |
|---|---|---|
| api | 8000 | **8100** |
| frontend | 5173 | **5273** |

Test runs never touch dev ports. `reuseExistingServer: false` always — a stale
server silently serving last round's build is a whole afternoon lost.

## API

- Routes are plural nouns: `/api/invoices`, not `/api/invoice` or
  `/api/getInvoices`.
- Status codes: `200` read, `201` create, `204` delete, `422` validation,
  `404` not found, `409` conflict. Never `200` with an error body.
- Validation errors return `{ "error": str, "field": str | None }`. One field
  per response — the first failure.
- Request and response bodies are Pydantic models. No bare dicts across a route
  boundary. Response models are explicit on the decorator so the OpenAPI schema
  is accurate.
- Timestamps are UTC, ISO-8601 with a `Z` suffix, named `createdAt` /
  `updatedAt` in JSON.
- JSON field names are `camelCase`; Python attributes are `snake_case`. The
  Pydantic model owns the aliasing.

## Money

Integer minor units only, field suffix `Cents`: `amountCents`. No floats
anywhere on the path — not in the model, not in the API, not in the frontend.
Formatting happens at render time only.

## Database

- Table names plural `snake_case`. Primary key is `id`, a UUID.
- Every foreign key has an index. Every migration is reversible.
- No business logic in the database: no triggers, no stored procedures.
- Enum-like columns are text with a CHECK constraint, not a Postgres ENUM type —
  altering an ENUM in a migration is more pain than it is worth.

## Frontend

- `data-testid` values are kebab-case, prefixed with the entity:
  `invoice-row`, `invoice-submit`, `invoice-empty`.
- One testid per interactive element and per list container. Rows carry the
  same testid; tests count them.
- API types are generated from the OpenAPI schema into `frontend/src/api/types.ts`.
  Never hand-written, never hand-edited.
- No `any`, no `as any`, no `@ts-expect-error`.

## Tests

- `api/tests/` — pytest, backend only. Its own Postgres container.
- `frontend/src/**/*.test.tsx` — vitest, component only. No network.
- `tests/contract/` — Playwright, the only place that knows both sides exist.
  Frozen once written for an item.
- Fixtures are named and seeded over HTTP: `POST /__test__/seed/<name>`.
  Fixture names are declared in the spec, never invented by the test-author.
- `/__test__/*` routes are mounted only when `APP_ENV=test`, and the app refuses
  to start with `APP_ENV=test` against a non-localhost `DATABASE_URL`.

## Auth

Handled by middleware. Assume `request.state.user_id` exists in any authenticated
route. Items do not implement auth unless the spec says so.

## Git

- One commit per PASSed item: source, spec, contract tests, all verdicts.
- Commit `.claude/agents/`, `.claude/settings.json`, `docs/`, `specs/`,
  `verdicts/`. Gitignore `.claude/settings.local.json`.
