<!-- Regenerable orientation INDEX for RDF Fingerprinter WS. Auto-loaded into every session (first ~200
     lines) — keep it ≤200 lines and curate ruthlessly. This is an INDEX, NOT authority: the truth
     is openspec/specs/ (durable capability specs) and openspec/config.yaml's `context:` field. If
     this note ever disagrees with openspec/specs/, specs/ wins. Stable, CONFIRMED facts only:
     codebase patterns, key paths. No session notes, no unverified conclusions, no epic detail
     (in-flight work lives in openspec/changes/). One-line entry per linked note. -->

# Project Memory (index) — RDF Fingerprinter WS

## Project Overview

- Structural fingerprinting of RDF files and SPARQL endpoints: Flask API/UI + Celery, wrapping `rdf-fingerprinter`.
- Top-level package: `fingerprinter/` (no `/src`). Branches: off `develop`, PRs into `develop`; `main` = releases.
- Layers: `bootstrap` over `entrypoints` and `adapters`, over `services`, over `domain` (import-linter, `make check-architecture`).
- Tooling: uv (`pyproject.toml`, `uv.lock`, Python 3.13); Ruff, mypy, import-linter, pytest (`pytest.ini`); `make check-all` is the gate.
- Method: developer runbook `docs/modules/ROOT/pages/develop/` (Antora); `make check-docs`, `make build-docs`.

## Spine (where work and truth live)

- EPIC ≡ `openspec/changes/<id>/proposal.md`; PLAN ≡ `design.md` + `tasks.md`.
- Durable truth: `openspec/specs/`. Orientation: `openspec/config.yaml: context:`.
- Drive with `/opsx:*` (propose, explore, apply, sync, archive). Golden thread: cite your parent.

## Reference

<!-- Pointers to in-repo reference material agents reuse. One line each.
     [code-anatomy.md](code-anatomy.md) — tier/layer dependency spec feeding .importlinter -->

## Key Decisions

<!-- yyyy-mm-dd: durable decision, in one line. Append; never rewrite history.
     (Authored decisions belong in the spine: proposal.md "Key decisions" / design.md "Decisions".) -->

## Gotchas

- `rdf-fingerprinter` 3.x requires Python >=3.12 (the old 0.3.x did not install on 3.12+).
- Settings and secrets live in the git-ignored `infra/.env` (template `infra/.env.example`); the keys once committed in `docker/.env` are burned.
- `resources/templates/json/` is a stub (no `main.json`); the library has no JSON report.
