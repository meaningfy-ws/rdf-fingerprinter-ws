# Clarity gate — PLAN (design.md + tasks.md)

Full gate (13 items, 6 criteria), scored by an independent agent, 2026-11-08.

| Pass | Score | Result |
|---|---|---|
| 1 | 8.3 / 10 | Fail. 12 gaps: job state for queued jobs (404), stage-1 ordering, two descriptions of the UI wiring, the library import rule vs `UsageError`, how `html`/`json` are produced, missing fixtures, no route table, vague references, an incomplete error matrix, scenarios missing, overlapping states, `env` handling. All fixed. |
| 2 | 9.2 / 10 | Pass. All 13 items pass. Remaining small gaps fixed afterwards: the library's operational variables (D-15), cancelling a queued job (*Cancel*), a spec clause import-linter cannot check (dropped; review lens), stage 2's API (D-17), test-map and CI details. |

Not checked by the gate (left to implementation): whether `p34_untyped_class` fires on a default
graph (task 3.2 has a fallback), `lint-imports` on a temporary package copy (task 2.6), Connexion 3
and Celery on Python 3.13.
