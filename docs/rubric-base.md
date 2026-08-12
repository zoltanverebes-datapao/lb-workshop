# Standing rubric criteria

These apply to **every** item. Specs do not restate them; specs number their own
criteria from `C1`. The evaluator grades these in addition to the spec's.

- **S1** — Full gate green: `bash scripts/verify.sh` exits 0.

- **S2** — Migration present: if the diff touches `api/app/models/`, a new
  revision exists under `api/alembic/versions/`.
  Verified by: `git diff --name-only` and `ls api/alembic/versions/`

- **S3** — Migration applies to an empty database: `alembic upgrade head`
  succeeds during Playwright's `webServer` start.

- **S4** — Migration is reversible: `alembic downgrade -1 && alembic upgrade head`
  succeeds, and `downgrade` is implemented rather than `pass`.

- **S5** — API types in sync: `frontend/src/api/types.ts` is regenerated from the
  OpenAPI schema and committed.
  Verified by: `npx openapi-typescript http://localhost:8100/openapi.json --check`

- **S6** — Test-only routes are unreachable in normal operation: `/__test__/*`
  returns 404 when `APP_ENV` is unset.
  Verified by: `uv run pytest api/tests/test_guards.py`

- **S7** — No type escape hatches added: the diff introduces no new
  `# type: ignore`, `: any`, `as any`, or `@ts-expect-error`.
  Verified by: `git diff | grep -nE '# type: ignore|: any|as any|ts-expect-error'`
  returns nothing.

- **S8** — Scope respected: no file outside the spec's `Scope: In` list is
  modified, except `api/alembic/versions/**`, `api/uv.lock`,
  `frontend/package-lock.json`, and `frontend/src/api/types.ts`.
  Verified by: `git diff --name-only`

- **S9** — Contract tests frozen: `git diff <base-sha> -- tests/contract/` is
  empty. Any change here is an automatic FAIL.

- **S10** — No secrets or connection strings committed.
  Verified by: `git diff | grep -nEi 'postgres://|password\s*=|api[_-]?key'`
  returns nothing outside test fixtures.

## Amending this file

Add a criterion only after a real FAIL showed it was missing. Date the entry.
When a criterion changes, note it in the first spec that uses the new form —
otherwise a builder follows the old doc and the critic grades against the new
one.
