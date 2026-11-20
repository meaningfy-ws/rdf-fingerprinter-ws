# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.0.0] - 2026-11-20

The first release since 2.0.2 (2022): a rewrite on `rdf-fingerprinter` 3.7, with a new user
interface and a hardened container stack. OpenSpec changes `upgrade-fingerprinter-library`,
`modernise-user-interface`, `harden-deployment` and `improve-ui-footer`.

### Changed (BREAKING)

- API: a report is downloaded by format name, `GET /reports/{uid}/{format}` with `format` one of
  `html`, `json`, `shacl`, `puml`, `svg`, `pattern`, `shex`, `pitfalls` or `zip`; a format of several
  files comes as a zip, and `GET /reports/{uid}/{format}/{file}` serves one file. The old
  `?report_type=` query is gone.
- API: a job has a state (`queued`, `running`, `completed`, `completed_with_failures`, `failed`,
  `cancelled`) with its failure reason and the measurements that failed. `POST` answers `202` with the
  job id.
- API: deleting a job that is `queued` or `running` answers `409`; cancel it first with
  `DELETE /tasks/{task_id}`, which answers `409` for a finished job.
- Custom report templates are removed: the library renders every report.
- Errors are `application/problem+json`.
- Both Flask secret keys (`RDF_FINGERPRINTER_API_SECRET_KEY`, `RDF_FINGERPRINTER_UI_SECRET_KEY`)
  have no default; the service does not start without them.
- Reports and jobs written by 2.x are not migrated.

### Added

- API: `GET /endpoint-graphs?url=` lists an endpoint's named graphs (`502` when it cannot).
- `rdf-fingerprinter` 3.7.1: every report format and the pitfall scan; the named graphs of an endpoint
  are profiled when none is selected; a query has a deadline per attempt and an answer is capped at
  `RDF_FINGERPRINTER_MAX_ANSWER_BYTES` (default 256 MiB).
- Limits: an endpoint URL carrying a user name or password is refused (`400`); uploads are capped by
  `RDF_FINGERPRINTER_MAX_UPLOAD_MB` (default 512; `413`); an unavailable broker answers `503`.
- UI: a console with live job state, a job page with the report, class diagrams and downloads,
  delete and cancel with confirmation, a graph picker for endpoints, and
  `RDF_FINGERPRINTER_UI_SECURE_COOKIES`; a footer with Meaningfy, the licence and the version.
- A PlantUML server (`SANDBOX` profile) that renders the class diagrams.
- `infra/`: multistage non-root images (API, UI, worker) on Python 3.13, `infra/compose.yaml`,
  `infra/.env.example`; `make init-env`, `up`, `up-dev`, `up-deps`, `down`, `rebuild`, `logs`,
  `run-api`, `run-ui`, `run-worker`.
- Images are published to `ghcr.io/meaningfy-ws/rdf-fingerprinter-ws-{api,ui,worker}` on each release.
- `SECURITY.md`, this changelog, container tests (integration and e2e) in CI.

### Changed

- Python 3.13 and uv (`pyproject.toml`, `uv.lock`) replace `requirements/` and `setup.cfg`; Flask 3,
  Connexion 3, Celery 5.7.
- The `fingerprinter` package is layered (`domain`, `services`, `adapters`, `entrypoints`,
  `bootstrap`); import-linter enforces it.
- gunicorn serves the API with `uvicorn_worker.UvicornWorker` (the `uvicorn-worker` package).
- GitHub Actions are pinned to commit SHAs.

### Removed

- `docker/` and its committed `.env` (the keys in it are burned: never reuse them); `bash/` and the
  `start-services` / `stop-services` targets; `curl-examples.md` (folded into the README); Docker Hub
  publishing (`package.yml`).

### Security

- `infra/compose.yaml` isolates the stack: the `app`, `work` and `monitor` networks are internal; an
  nginx edge proxy publishes the UI and the API on `127.0.0.1`; a Squid egress proxy is the only way out
  for the API and the worker and refuses loopback, private, link-local and shared addresses, so a job
  against `169.254.169.254`, a service of the stack or `127.0.0.1` fails (SSRF).
- Redis, Fuseki and PlantUML are not published by `make up`; `make up-dev` and `make up-deps` add
  `infra/compose.dev.yaml`, which publishes them on `127.0.0.1`.
- Secrets are read from the environment only and are not logged; each container holds only its
  secrets (no `env_file`), the worker needs no Flask key; `.env` files are git-ignored and kept out of
  the images. `make init-env` writes `infra/.env` with random secrets; `make check-env` refuses
  placeholder secrets; `make down` needs no `infra/.env`.
- The UI's forms carry CSRF tokens; its pages refuse framing by other sites.
