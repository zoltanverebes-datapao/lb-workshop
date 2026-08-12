# Working agreement

## The loop

Work **one backlog item at a time**. Each item has an id (e.g. `INV-14`).

```
spec  →  validate assumptions  →  contract tests  →  code  →  verdict
                                                          ↑         │
                                                          └─ FAIL ──┘
```

`PASS` is the only exit. Nothing is committed to `main` before a PASS.

### Stages

| # | Stage | Agent | Output | When |
|---|-------|-------|--------|------|
| 0 | Spec | `spec-writer` | `specs/<id>.md` | Once, human-approved before stage 0.5 |
| 0.5 | Validate assumptions | `assumption-validator` | detailed report, verdict PASS/FAIL/BLOCKED | Once, after stage 0 approval, before stage 1 |
| 1 | Contract tests | `test-author` | `tests/contract/<id>.spec.ts` | Once, frozen after |
| 2 | Code | `generator` | code under `backend/` and `web/` | Every round |
| 3 | Grade | `evaluator` | `verdicts/<id>-r<n>.md` | Every round |

**Stage 0 requires human approval.** The spec-writer emits an
`## Assumptions — CONFIRM` block. Do not proceed to stage 0.5 until a human has
reviewed and the block has been resolved and removed.

**Stage 0.5 validates the environment.** The assumption-validator reads the spec's
assumptions and checks if the current project state matches. Verdict is PASS/FAIL/BLOCKED.
- `PASS` → proceed to stage 1
- `FAIL` → human fixes issues, re-run validator
- `BLOCKED` → human decision needed

**Stage 1 happens before any implementation exists.** The contract tests must
fail red before stage 2 starts. After stage 1 is committed, `tests/contract/`
is frozen for the remainder of the item.

### Pre-implementation (one-time)

1. Human approves spec (removes `## Assumptions — CONFIRM` section).
2. Delegate to `assumption-validator` with the spec id.
3. Read the verdict:
   - `PASS` → proceed to step 4
   - `FAIL` → human fixes issues, re-run validator
   - `BLOCKED` → stop and report to human; human decides and re-runs
4. Delegate to `test-author` with the spec id (contract tests are written once, frozen after).

### Round N (implementation lead behaviour)

1. Delegate to `generator` with the item id and the newest verdict path (if any).
2. Delegate to `evaluator` with the item id and round number `n`.
3. Read the verdict line:
   - `PASS` → commit and stop.
   - `FAIL` → `n = n + 1`, go to 1.
   - `BLOCKED` → stop and report to the human. **Does not consume a round.**
4. After **3** consecutive FAILs, stop and escalate. Three FAILs means the spec
   is wrong, not the code. Do not start a fourth round.

### Commit

On PASS, commit as one change: source, `specs/<id>.md`,
`tests/contract/<id>.spec.ts`, and every `verdicts/<id>-r*.md`. The verdicts are
history and are kept deliberately — do not squash them away.

(Assumption validation reports are not committed—they are one-time diagnostics.
Only commit on final PASS.)

## Layout

```
backend/                FastAPI, uv, Yoyo, pytest
web/                    React + Vite, vitest
tests/contract/         Playwright — the only code that sees both sides
tests/setup/            Postgres container, global setup
scripts/verify.sh       the single verification entry point
specs/<id>.md           the contract for one item
verdicts/<id>-r<n>.md   one per round
docs/conventions.md     house rules, inherited by every spec
docs/rubric-base.md     standing criteria, inherited by every rubric
docs/glossary.md        canonical domain terms and field names
.claude/agents/         role definitions
```

## Inherited documents

Every agent reads these at the start of every task, in addition to the spec:

- `docs/conventions.md`
- `docs/rubric-base.md`
- `docs/glossary.md`

Specs do **not** restate their contents. If a spec contradicts a convention,
that is a defect in one of the two — stop and report it rather than picking.

## Verification

`scripts/verify.sh` is the only verification entry point. It owns the whole
gate. Never conclude that something passes without running it.

Ports are `8100` (api) and `5273` (web) in test. Never `8000` or `5173` — those
belong to a human's dev server.

## Non-negotiable

- Every rubric criterion names a command. Anything that does not is a note.
- The critic runs the tests itself. A builder's claim is not evidence.
- Infrastructure failure is `BLOCKED`, never `FAIL`.
- `tests/contract/` is never edited to make a round pass.