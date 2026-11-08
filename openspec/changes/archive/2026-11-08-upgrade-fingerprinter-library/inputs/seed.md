---
kind: elicitation record (secondary; superseded by proposal.md, never groomed)
---

# Elicitation — upgrade the fingerprinter library

Answers the developer gave on 2026-11-08 while shaping this EPIC, in the order asked. Each
recommendation offered is marked; the answer is what the developer chose.

## Origin

- The developer asked to set the repo up like rdf-persistence (uv) with the agent workflow of
  mapping-workbench-v2, then to shape two EPICs: adopt the latest `rdf-fingerprinter`, and
  modernise the UI. The non-code setup landed in PR #23.
- **Python and the setup (asked before PR #23).** Offered: a uv setup on Python 3.11 now, the move to
  3.12+ in this EPIC (recommended); or fold everything into this EPIC. **Chosen: fold.** The uv,
  Python and tooling modernisation is part of this EPIC.

## Round 1

| Question | Recommended | Chosen |
|---|---|---|
| Which outputs does a job produce? | Parity (main.html, profile.json, zip) | **Everything in the zip**: main.html, profile.json, SHACL, PlantUML, pattern schema, ShExC, pitfalls |
| The custom report templates in `resources/templates/` | Drop them | **Drop them** (and the template volume, `set-report-template`) |
| May this EPIC change the REST API? | Keep it compatible | **Allow breaking changes** |
| Graph scope when none is selected | Library default (all graphs) | **Library default**: the default graph and every named graph |

## Round 2

| Question | Recommended | Chosen |
|---|---|---|
| How far to reshape the API | Minimal, report-driven: downloads by format name | **Minimal, report-driven** |
| Web stack | Latest of the same stack (Flask 3, Connexion 3, Celery 5.5) | **Latest of the same stack** |
| Python | 3.13 | **3.13** |
| Pitfall scan | On by default | **On by default** |

## Round 3

| Question | Recommended | Chosen |
|---|---|---|
| Layering | Fix the import cycle, enforce the current layers | **Full cosmic-python** (domain, ports in services, adapters, composition root) |
| Quality gates on legacy code | Full gates, fix the debt | **Full gates, fix the debt** (Ruff, mypy, import-linter, coverage ≥ 80 %) |
| Infrastructure | `infra/` + GHCR | **`infra/` + GHCR**; Docker Hub publishing removed |
| Committed secret keys | Not deployed / unsure: `.env.example`, keys treated as burned | **Not deployed / unsure** |

## Round 4

| Question | Recommended | Chosen |
|---|---|---|
| How to cut the work | One EPIC, staged | **One EPIC, staged** |
| The UI during this EPIC | Keep it working, minimal | **Keep it working, minimal** |
| `bash/` scripts | Remove | **Remove** |
| What the EPIC must prove | — | **All four**: endpoint job → all outputs; file job cleans up its dataset; failures are visible; real stack end to end in CI |

## UI technology (asked between rounds)

The developer asked whether to move the UI to Next.js or stay on Flask. Answer given: Flask
(Jinja + htmx) covers a job console; Next.js pays off for an interactive explorer of fingerprints,
and is MWB2's stack. **Chosen: keep Flask for now.** The UI EPIC decides further; this EPIC gives the
API a clean JSON contract either way.

## Leader's choices (the developer may overrule)

Recorded in the EPIC as decisions marked *leader's choice*:

- No prefix.cc lookup at run time (offline, repeatable runs; the library's packaged prefixes apply).
- A job whose report was written with failed measurements ends as *completed with failures*, with
  the failures listed, not as a plain success.
- Reports written by the 0.3.1 service are not migrated (no known deployment).
