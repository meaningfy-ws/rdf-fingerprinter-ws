---
kind: analysis brief (secondary; superseded by proposal.md, never groomed)
---

# Gap report — rdf-fingerprinter-ws against the Meaningfy standard and library 3.5.0

Audit of `develop` at `113eb6b` (2026-11-08), against the project-setup standard (reference
repositories: rdf-persistence for uv, mapping-workbench-v2 for the agent workflow) and against
`rdf-fingerprinter` 3.5.0. Only detected gaps are listed.

## Library

| Area | Today | 3.5.0 |
|---|---|---|
| Version | `rdf-fingerprinter~=0.3.1` (installs on Python ≤ 3.11) | 3.5.0, Python ≥ 3.12 |
| Entry point | `fingerprint.service_layer.handlers.generate_endpoint_fingerprint_report`, called twice per job (HTML template, JSON template) | removed in 3.0; `fingerprint_report(url, folder, settings, *, formats, options, template, user_prefixes, prefix_list, checks, sparql, renderer) -> (Path, ProfileRun)` |
| Outputs | `main.html` from a custom template; a JSON "report" from a stub template | `main.html` and `profile.json` always; `shacl`, `puml`, `pattern`, `shex`, `pitfalls` on request |
| Templates | `resources/templates/{html,json}` (incl. a "cellar" config), a Docker volume, `make set-report-template` | templates render a `ProfileDocument` view; the old templates no longer render |
| Graph scope | none selected → default graph only | none selected → default graph and every named graph (2.0) |
| Failures | errors printed into the report | `ProfileRun.failures`; usage errors raised before any query |
| Logging | needs `logging.conf` in the working directory | configures nothing on import |

## Repository

| Dimension | State |
|---|---|
| Dependencies | pip `requirements/{common,dev,prod}.txt` + `requirements.txt` + `setup.cfg`; no lock |
| Python | 3.8 in CI and Docker |
| Lint / types / architecture | none (no Ruff, mypy, import-linter) |
| Tool config | pytest config in `setup.cfg` with coverage flags in `addopts` |
| Layers | `entrypoints → services → adapters`, but `adapters/celery.py` imports `services.report_handling` and services import adapters (a cycle); no domain layer |
| Tests | 48 tests in `tests/unit/` only; no tier folders or markers; `selenium` imported in `conftest.py`; no coverage floor |
| Web stack | Flask 2.2, Connexion 2.14, Flask-WTF 1.2, Celery 5.3, redis 5.0, flower 2.0 |
| Infra | `docker/` (api and ui images on `python:3.8.18-bullseye`, root user, pip), compose with the source mounted; `stain/jena-fuseki` |
| Secrets | Flask secret keys committed in `docker/.env` and `bash/.env` |
| Scripts | `bash/` Red Hat/Ubuntu install and gunicorn scripts, with Makefile targets |
| CI | `tests.yml` (Python 3.8, every push, Codecov); `package.yml` pushes images to Docker Hub on release |
| Makefile | no `install`/`check-all`/`lint`/`typecheck`/`check-architecture` targets |
| Release | no `CHANGELOG.md`, `SECURITY.md`, `VERSION` |
| Already conformant | top-level package (no `/src`); `AGENTS.md` + `CLAUDE.md` pointer; `openspec/` spine; Antora docs |
