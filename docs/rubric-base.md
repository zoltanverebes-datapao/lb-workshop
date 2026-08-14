# Standing rubric criteria

These apply to **every** item. Specs do not restate them; specs number their own
criteria from `C1`. The evaluator grades these in addition to the spec's.

- **S1** — Full gate green: `bash scripts/verify.sh` exits 0.

- **S2** — Migration present: if the diff changes the database schema, a new
  revision exists under `backend/migrations/`.
  Verified by: `git diff --name-only` and `ls backend/migrations/`

- **S3** — Migration applies to an empty database: applying all pending Yoyo
  migrations (`backend.apply_migrations(backend.to_apply(migrations))`, as in
  `app/main.py`'s lifespan) succeeds during Playwright's `webServer` start.

- **S4** — Migration is reversible: rolling back the newest migration and
  reapplying it (`backend.rollback_migrations(backend.to_rollback(migrations)[:1])`
  then `backend.apply_migrations(...)`) succeeds, and each `step`'s `rollback`
  is real SQL rather than a no-op.

- **S5** — API types in sync: `frontend/src/api/types.ts` is regenerated from the
  OpenAPI schema and committed.
  Verified by: `npx openapi-typescript <schema-file-or-url> -o frontend/src/api/types.ts && git diff --exit-code -- frontend/src/api/types.ts`
  (openapi-typescript v7 has no `--check` flag; a clean `git diff` after
  regenerating is the equivalent guarantee.)

- **S6** — Test-only routes are unreachable in normal operation: `/__test__/*`
  returns 404 when `APP_ENV` is unset.
  Verified by: `uv run pytest backend/tests/test_guards.py`

- **S7** — No type escape hatches added: the diff introduces no new
  `# type: ignore`, `: any`, `as any`, or `@ts-expect-error`.
  Verified by: `git diff | grep -nE '# type: ignore|: any|as any|ts-expect-error'`
  returns nothing.

- **S8** — Scope respected: no file outside the spec's `Scope: In` list is
  modified, except `backend/migrations/**`, `backend/uv.lock`,
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

**2026-08-13** — S2–S6, S8 referred to `api/`, alembic, and an
`openapi-typescript --check` flag that never matched this repo (`backend/` +
Yoyo migrations, no such flag exists). S7's evaluator caught the mismatch;
S8's spec-writer flagged it again rather than pick silently. Corrected in
place — see `specs/S8.md` for the first item graded under the corrected
text.
