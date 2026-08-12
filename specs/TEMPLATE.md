# <ID>: <one-line title>

Status: **PENDING**

Inherits: `docs/conventions.md`, `docs/rubric-base.md`, `docs/glossary.md`

## Goal
<2–3 sentences. What changes for the user when this is done. Not how.>

## Scope
In:
- `api/app/...`
- `frontend/src/...`

Out:
- <the adjacent thing a reasonable builder would drift into> (<owning item id>)
- <another>

## Interface contract
Everything the test-author needs. It never sees the implementation, so anything
missing here becomes a guess that costs a round.

Routes:
- `GET  /api/<resource>`   200 → `{ <resource>: T[] }`
- `POST /api/<resource>`   201 → `{ <resource>: T }`
                           422 → `{ error, field }`

Shape:
```
{ id: string, ..., createdAt: string }
```

Validation:
- `<field>` — <rule>

Test IDs: `<entity>-list`, `<entity>-row`, `<entity>-empty`, `<entity>-submit`,
          `<entity>-error`

Accessible names: <button/form names the tests can target by role>

Fixtures:
- `<entity>/empty` — no rows
- `<entity>/three` — three rows, createdAt 3/2/1 days ago

## Rubric
Standing criteria in `docs/rubric-base.md` also apply. Number from C1.

- C1: <observable behaviour, stated so two people could not disagree>
      — verified by: `<exact command>`
- C2: <a rejection case — what happens on invalid input, and that no row is
      created>
      — verified by: `<exact command>`
- C3: <an ignored-input case, if the shape allows one>
      — verified by: `<exact command>`

## Notes
<Constraints, prior art, gotchas. Anything you could not phrase as a command
belongs here, not in the rubric.>

## Assumptions — CONFIRM
<Written by spec-writer. Removed by a human on approval. Stages 1–3 do not run
while this section is present.>
- A1:
