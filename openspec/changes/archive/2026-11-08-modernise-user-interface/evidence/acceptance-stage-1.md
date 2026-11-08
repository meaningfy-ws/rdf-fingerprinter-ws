# Acceptance demo — UI stage 1 (Console)

> Prepared by the leader on 2026-11-08; **validation is the developer's** (sign-off at the end).
> Change `modernise-user-interface`, task 1.7.

## Where

The demo stack runs from branch `feat/ui-stage-1-console`: UI http://localhost:8020, API
http://localhost:4020/ui (Swagger), Fuseki and Redis in Docker. Older jobs made before this stage
still show their outputs.

## What to try

1. **Jobs** (`/`): one list, newest first; Source with its kind line, Started ("5 min ago", exact
   time on hover), the status badge and note, "Open report" and "Download all (.zip)" for finished
   jobs; the ⋯ menu ("Delete…", or "Cancel job…" while active); the filters All · In progress ·
   Finished · Failed or cancelled.
2. **New job** (`/jobs/new`): "From an endpoint" — enter `http://localhost:33040/demo/sparql`,
   "Start fingerprinting"; back on Jobs the row moves Queued → Running… → Done without a reload, and
   polling stops. Try `ftp://x` (the sentence next to the field) and a `.docx` file (the accepted
   types).
3. **Delete…** on a finished job: "Keep it" leaves it, "Delete report" removes it.
4. Switch the system to dark mode, and narrow the window to phone width.

## Checked by the agents

- `make check-all`: 496 tests; `make test-containers`: 46 tests, green twice.
- Browser journeys (start and watch a job finish; delete with confirmation; keyboard only).
- axe-core WCAG 2.2 AA: no violation on Jobs, New job (both tabs) and the confirmation, light and
  dark, and at 360 px; no external asset requested.
- Five-lens review, findings fixed (design.md, "Stage-1 review", S1-1 to S1-8).

- [x] Accepted by the developer (2026-11-08): "look fine, go ahead".
