> Derives from: EPIC `upgrade-fingerprinter-library` (`proposal.md`, DEC-1 to DEC-16).

## Context

The service is a Flask/Connexion API, a Flask UI and a Celery worker around `rdf-fingerprinter`
0.3.1, on Python 3.8 (audit: `inputs/gap-report.md`). Per job it calls the removed
`generate_endpoint_fingerprint_report` twice (HTML and JSON templates), zips both and writes a
`meta.json` only when the job succeeds. File jobs go through a temporary Fuseki dataset
(`fingerprinter/services/handlers.py` `upload_file_to_dataset`, already deleting the dataset in a
`finally`). `fingerprinter/adapters/celery.py` and `fingerprinter/services` import each other. There
are 48 tests, all in `tests/unit/`.

Library 3.5.0 facts this plan relies on (checked in `/home/lps/work/repos/rdf-fingerprinter`):

- `fingerprint.service_layer.settings.resolve_settings(cli, env, selected_graphs, config)` builds
  the `Settings`; `pitfall_scan` is a documented setting (`docs/.../statistics.adoc#settings`), off
  by default; empty `selected_graphs` means all graphs; `env=None` reads the library's collection
  settings from its `RDF_FINGERPRINTER_*` variables, `env={}` reads none.
- Independently, `fingerprint_report` and `generate_representations` call `validate_config()`, which
  reads the library's eight operational variables from the real environment on every call:
  `RDF_FINGERPRINTER_{PROFILE_FILE,RETRY_BACKOFF_SECONDS,TIMEOUT_MARKERS,ERROR_EXCERPT_LENGTH,SHAPES_NAMESPACE,DEFAULT_GRAPH_LABEL,PREFIXES_FILE,PREFIX_LOOKUP}`.
- `fingerprint.service_layer.handlers.fingerprint_report(url, folder, settings, *, formats=(),
  prefix_list=None, ...)` writes `main.html` and `profile.json` into `folder` and returns
  `(Path, ProfileRun)`; `run.failures` lists the measurements that failed. Usage errors raise
  `UsageError`, documented as a `ValueError`, before any query; an endpoint unreachable at the start
  raises `fingerprint.adapters.exceptions.EndpointUnreachable`.
- `fingerprint.service_layer.representations.generate_representations(run, folder, formats)`
  writes the given formats into `folder` and returns the files written; all six names of
  `RepresentationFormat` (`shacl`, `puml`, `doc`, `pattern`, `shex`, `pitfalls`) are registered
  generators.

## Goals / Non-Goals

**Goals:**
- The four stages of the EPIC, each one PR into `develop` with `make check-all` green.
- The three capabilities of the spec deltas: `fingerprinting-jobs`, `report-access`,
  `package-boundaries`.
- The EPIC's success measure, shown at the acceptance demo.

**Non-Goals:**
- Everything in the EPIC's no-gos. In particular: no per-job settings, no format selection, no
  authentication, no UI redesign, no data-profiling CLI.

## Decisions

- **D-1 Package layout** (DEC-8):

  | Module | Holds |
  |---|---|
  | `fingerprinter/domain/model.py` | `ReportFormat` (enum: `html`, `json`, `shacl`, `puml`, `pattern`, `shex`, `pitfalls`, `zip`), `JobState` (enum, D-5), `Source` (endpoint URL or file name, graphs), `JobRecord` (id, source, created_at, state, reason, failures, formats), `FingerprintOutcome` (files per format, failures) — frozen dataclasses |
  | `fingerprinter/domain/exceptions.py` | `InvalidSource`, `UnsupportedFileType`, `JobNotFound`, `FormatNotAvailable`, `QueueUnavailable` |
  | `fingerprinter/services/ports.py` | the ports of D-2 |
  | `fingerprinter/services/jobs.py` | `submit_endpoint_job`, `submit_file_job`, `run_endpoint_job`, `run_file_job`, `job_status`, `active_jobs`, `cancel_job` |
  | `fingerprinter/services/reports.py` | `list_reports`, `report_download`, `delete_report`, `delete_all_reports` |
  | `fingerprinter/adapters/fingerprint_library.py` | `LibraryFingerprinter`, the only importer of `fingerprint` |
  | `fingerprinter/adapters/fuseki.py` | `FusekiDatasetStore` (Fuseki admin API `/$/datasets`, `requests`) |
  | `fingerprinter/adapters/file_job_store.py` | `FileJobStore` (the reports folder: `meta.json`, format folders, zips) |
  | `fingerprinter/adapters/file_upload_store.py` | `FileUploadStore` (the upload folder `db/`) |
  | `fingerprinter/adapters/celery_queue.py` | `CeleryJobQueue` (sends tasks by name, revokes) |
  | `fingerprinter/entrypoints/api/` | Connexion 3 app factory `create_app(services)`, handlers, `openapi/fingerprinter.yml` |
  | `fingerprinter/entrypoints/ui/` | the Flask 3 UI `create_app(api_base_url)` and its HTTP client of the API (`api_wrapper.py`) |
  | `fingerprinter/entrypoints/worker/tasks.py` | `register_tasks(celery_app, services)`: the tasks `fingerprint_endpoint` and `fingerprint_file` |
  | `fingerprinter/config.py` | `Settings` read from `RDF_FINGERPRINTER_*` variables (D-7) |
  | `fingerprinter/bootstrap.py` | the composition root: builds adapters and services, exposes `api_app()`, `ui_app()` and `celery_app` |

- **D-2 Ports** (`fingerprinter/services/ports.py`, `typing.Protocol`):
  - `Fingerprinter.fingerprint(endpoint_url, graphs, work_folder) -> FingerprintOutcome`
  - `DatasetStore.create(name)`, `.load_file(name, path)`, `.delete(name)`, `.sparql_url(name) -> str`
  - `JobStore.create(record)`, `.get(id) -> JobRecord`, `.list() -> list[JobRecord]`,
    `.set_state(id, state, reason=None, failures=())`, `.save_outputs(id, outcome)`,
    `.discard_outputs(id)`, `.file_for(id, format) -> Path`, `.delete(id)`, `.delete_all()`
  - `UploadStore.save(job_id, stream, filename) -> Path` (under `db/<job id>/`), `.discard(job_id)`
  - `JobQueue.submit_endpoint(job_id, url, graphs)`, `.submit_file(job_id, path)`, `.cancel(job_id)`

- **D-3 Report layout.** `reports/<job id>/meta.json` (the job record), and once outputs exist one
  folder per format: `html/main.html`, `json/profile.json`, `shacl/`, `puml/`, `pattern/`, `shex/`,
  `pitfalls/`, plus `report.zip` (every format folder). `LibraryFingerprinter` calls
  `fingerprint_report(..., formats=())` into the work folder, moves `main.html` to `html/` and
  `profile.json` to `json/`, then calls `generate_representations(run, <format folder>, [format])`
  once for each of `shacl`, `puml`, `pattern`, `shex`, `pitfalls`, and sorts files by the list each
  call returns, never by the library's file names.
- **D-4 API routes** (DEC-5). Changes from today are marked.

  | Method and path | Request | Success | Errors |
  |---|---|---|---|
  | `POST /fingerprint-sparql-endpoint` | JSON `{sparql_endpoint_url, graphs?}` | **`202`** `{task_id}` (was 200) | `400`, `503` |
  | `POST /fingerprint-file` | multipart `data_file` | **`202`** `{task_id}` (was 200) | `415`, `503` |
  | `GET /reports` | — | `200` list of job records | — |
  | **`GET /reports/{uid}`** | — | `200` the job record (was: a download by `report_type`) | `404` |
  | **`GET /reports/{uid}/{format}`** (new) | `format` ∈ D-1 `ReportFormat` | `200` the file, or `<uid>-<format>.zip` when the format has several files | `400`, `404` |
  | `DELETE /reports/{uid}` | — | `200` `{message}` | `404` |
  | `DELETE /remove-reports` | — | `200` `{message}` (an empty store also answers `200`; was `404`) | — |
  | `GET /tasks/active` | — | `200` the job records in `queued` or `running` (was: Celery's active list) | — |
  | `GET /tasks/{task_id}` | — | `200` `{task_id, state, reason, failures}` (**new body**) | `404` |
  | `DELETE /tasks/{task_id}` | — | `200` `{message}`; the job becomes `cancelled` | `404`, `409` when not `queued`/`running` |

  A job record in JSON: `{"id", "source": {"endpoint" | "file", "graphs"}, "created_at", "state",
  "reason", "failures", "formats"}`. Errors are problem responses (`application/problem+json`,
  Connexion's default) with `type` set per domain exception.
- **D-5 Job record and states.** `meta.json` is the single source of a job's state; Celery's result
  backend is not read. States: `queued` (written by `submit_*` before the task is sent), `running`
  (written by the worker when the task starts), `completed`, `completed_with_failures` (outputs
  saved; failures listed), `failed` (ended by an error; `reason` holds the message; no outputs
  kept), `cancelled` (ended by a client; no outputs kept). The job id is a `uuid4` string used as the
  Celery task id and the folder name. `404` means no `meta.json` for that id.
- **D-6 The worker.** `bootstrap.celery_app` is the Celery app; `register_tasks` adds
  `fingerprint_endpoint` and `fingerprint_file`, each calling `services.jobs.run_*` with the
  bootstrapped dependencies. `CeleryJobQueue` sends by task name (`send_task`) and cancels with
  `revoke(terminate=True)`, so no adapter imports an entrypoint. Command:
  `celery -A fingerprinter.bootstrap:celery_app worker`. Celery settings: `task_track_started`
  off, `task_acks_late` off, no autoretry.
- **D-7 Configuration.** `fingerprinter/config.py` `Settings`, a frozen dataclass built by
  `Settings.from_env()`, read only by `bootstrap` (the settings pattern of the project-setup skill,
  no new dependency). It keeps the `RDF_FINGERPRINTER_*` names for the locations, ports,
  credentials, folders, time zone and Swagger switch, and drops the template, report-name and
  logger settings. The two Flask secret keys have no default: a missing key stops the app at start
  (DEC-13).
- **D-8 API runtime.** Connexion 3 `FlaskApp`, served by gunicorn with
  `uvicorn.workers.UvicornWorker`. Handlers reach the services through
  `flask.current_app.extensions["fingerprinter"]`, set by `create_app`. A handler maps a domain
  exception to its problem response in one error handler per exception.
- **D-9 UI.** A Flask 3 app (Flask-WTF forms, Jinja templates), a client of the API over HTTP
  (`requests`) only: it imports no service, adapter or `bootstrap` module. It changes only the
  report and job pages (spec `report-access`, "The UI offers every format") and its download route
  (`/reports/<id>/<format>`, proxying the API). Served by gunicorn.
- **D-10 Dependencies.** Exact pins in `pyproject.toml`, the latest releases on the day task 1.1
  runs (as `/home/lps/work/repos/rdf-persistence/pyproject.toml`), `rdf-fingerprinter==3.5.0`.
  Runtime: `rdf-fingerprinter`, `flask`, `flask-wtf`, `connexion[flask,swagger-ui,uvicorn]`,
  `celery[redis]`, `flower`, `requests`, `gunicorn`. Dropped: `SPARQLWrapper`, `eds4jinja2`,
  `rdflib`, `selenium`, `requests-toolbelt`, and `shortuuid`/`click` unless an import remains.
  Groups: `test` (pytest, pytest-bdd, pytest-cov, testcontainers, beautifulsoup4), `lint` (ruff,
  mypy, import-linter, types-requests), `dev` (pre-commit).
  *As built (task 1.1, 2026-11-08):* Celery resolved to 5.7.0 and Connexion to 3.3.0 (the current
  releases; DEC-6's "5.5" named the then-current minor). `pytz` is replaced by the standard
  `zoneinfo`; the Fuseki upload streams the file as the request body (Graph Store Protocol), so
  `requests-toolbelt` goes; the extension lookup that used `rdflib.util.guess_format` is a dict
  lookup, so `rdflib` goes too. The API's test client is Connexion 3's (Starlette, `httpx` style).
- **D-11 Tests.** Tier folders `tests/unit/`, `tests/feature/`, `tests/integration/`,
  `tests/e2e/`, markers set by path in `tests/conftest.py` with the `pytest_collection_modifyitems`
  hook of `/home/lps/work/repos/rdf-persistence/tests/conftest.py`. Unit and feature tests use the
  fakes of the ports in `tests/fakes.py`; feature tests are pytest-bdd scenarios in
  `tests/feature/fingerprinting_jobs.feature` and `tests/feature/report_access.feature`, each
  scenario named as its spec scenario. Integration tests run each adapter against a container
  (Fuseki, Redis), and `LibraryFingerprinter` against Fuseki; e2e tests run the API app with a real
  worker (`celery.contrib.testing.worker.start_worker`), Fuseki and Redis. Containers through
  `testcontainers`, started once per session.
- **D-12 Coverage.** The 80 % floor applies to the unit and feature lane (`make test`), with
  `fingerprinter/adapters/*` and `fingerprinter/bootstrap.py` omitted in `.coveragerc`; they are
  covered by `make test-containers`, reported without a floor (as
  `/home/lps/work/repos/rdf-persistence/.coveragerc` and its `Makefile`).
- **D-13 Fuseki image.** `stain/jena-fuseki`, at the newest tag whose admin API passes the
  `FusekiDatasetStore` integration tests (task 4.2); a different image is a change to this design
  first.
- **D-17 What stage 2 serves.** Stage 2 delivers the job record, so it also delivers the D-4
  routes that expose it: `GET /reports`, `GET /reports/{uid}`, `GET /tasks/active`,
  `GET /tasks/{task_id}`, `DELETE /tasks/{task_id}` and the `202` answers, with `formats` limited to
  `html` and `json`. `GET /reports/{uid}/{format}` serves `html`, `json` and `zip` in stage 2 and
  every format in stage 3. The UI's job page shows the new state from stage 2. API clients see the
  break from the stage-2 PR on.
- **D-14 Stage 1 is transitional.** Stage 1 keeps the old module structure and API contract, calls
  `fingerprint_report(..., formats=())` and serves `main.html` as `html`, `profile.json` as `json`
  and their zip as `zip`. The templates go in stage 1 (DEC-4), since they cannot render with 3.x.
- **D-15 Library settings.** `LibraryFingerprinter` calls `resolve_settings(env={},
  selected_graphs=graphs, config={"pitfall_scan": True})`, so collection settings never come from
  the worker's environment, and catches `ValueError` (the documented type of `UsageError`) and
  `EndpointUnreachable`. The library's eight operational variables (Context) are not supported by
  this service: `infra/.env.example`, the compose file and CI set none of them, and D-3 relies on
  the default `profile.json` name. The adapter imports only the modules named in D-16 (checked by
  the architecture review lens; import-linter cannot restrict submodules of an external package).
- **D-16 Import contracts** (spec `package-boundaries`), in `.importlinter`: layers
  `fingerprinter.bootstrap` > (`fingerprinter.entrypoints` | `fingerprinter.adapters`) >
  `fingerprinter.services` > `fingerprinter.domain`; `fingerprinter.config` imported only by
  `fingerprinter.bootstrap`; `fingerprinter.entrypoints.ui` imports no other `fingerprinter` module
  but `fingerprinter.entrypoints.ui`; `fingerprint` imported only by
  `fingerprinter.adapters.fingerprint_library`; the domain imports none of `flask`, `connexion`,
  `celery`, `requests`, `fingerprint`.

### Library dependencies

- **L-1** The API reference (`docs/modules/ROOT/pages/api-reference.adoc` in the library) lists
  only `shacl` and `puml` under `formats`, although all six generators are registered. Task 3.1
  confirms `pattern`, `shex` and `pitfalls` render through `generate_representations` and files a
  `documentation` issue in `meaningfy-ws/rdf-fingerprinter`; if one does not render, the task stops
  and files a `bug` issue instead (the strict rule).
- **L-2** The wheel ships no `py.typed` marker, so mypy treats `fingerprint` as untyped
  (`meaningfy-ws/rdf-fingerprinter#64`, filed in task 1.6). `mypy.ini` holds a section
  `[mypy-fingerprint.*] ignore_missing_imports = True`, named and scoped to that package; it changes
  no behaviour, only what mypy can check at the library boundary. The section is removed in the PR
  that raises the pin to a release that ships the marker. *Leader's choice:* the gate does not wait
  for the fix, since nothing in the service compensates for the gap.

## Algorithm / approach

**Endpoint job.** `submit_endpoint_job(url, graphs)` validates the URL (`http`/`https`, else
`InvalidSource`), makes a job id, writes the record (`queued`) through `JobStore.create`, and calls
`JobQueue.submit_endpoint`; if the queue raises, it sets the record `failed` ("queue unavailable")
and raises `QueueUnavailable`. The worker's `run_endpoint_job(job_id, url, graphs)` sets `running`,
makes a work folder, calls `Fingerprinter.fingerprint(url, graphs, work)`, then
`JobStore.save_outputs` and sets `completed` or `completed_with_failures`; on an exception it sets
`failed` with the message; in `finally` it removes the work folder. A record already `cancelled`
is never overwritten, and a task that finds its record `cancelled` after saving discards the
outputs (`JobStore.discard_outputs`).

**Cancel.** `cancel_job(id)` answers `409` unless the record is `queued` or `running`; it sets
`cancelled`, revokes the task (`JobQueue.cancel`), calls `JobStore.discard_outputs(id)`, and for a
file job `UploadStore.discard(id)` (a queued task never runs its `finally`). The dataset of a
running file job is removed by that task's `finally`, or, if `terminate` kills it first, by the
`task_revoked` fallback of *Risks*.

**File job.** `submit_file_job(stream, filename)` checks the extension against the supported list
(else `UnsupportedFileType`), saves the upload with `UploadStore`, writes the record and submits it
(on a queue error: the upload is discarded, the record set `failed`, `QueueUnavailable` raised). The
worker's `run_file_job(job_id, path)` names a dataset `fp-<job id>` and runs as the endpoint job
with `DatasetStore.sparql_url(name)` as the endpoint, between `DatasetStore.create` + `load_file`
before and, in `finally`, `DatasetStore.delete(name)` (a missing dataset is not an error) and
`UploadStore.discard(job_id)`.

**Worked example.** `POST /fingerprint-sparql-endpoint {"sparql_endpoint_url":
"http://fuseki:3030/test/sparql"}` → `202 {"task_id": "3f2c…"}` and
`reports/3f2c…/meta.json` with `"state": "queued"`. The worker writes `html/main.html`,
`json/profile.json`, `shacl/…`, `puml/…`, `pattern/…`, `shex/…`, `pitfalls/…`, `report.zip`, and
the record `{"id": "3f2c…", "source": {"endpoint": "http://fuseki:3030/test/sparql", "graphs": []},
"created_at": "…", "state": "completed", "reason": null, "failures": [], "formats": ["html", "json",
"shacl", "puml", "pattern", "shex", "pitfalls"]}`. `GET /reports/3f2c…/puml` →
`3f2c…-puml.zip`; `GET /reports/3f2c…/html` → `main.html`.

**Idempotency.** Tasks are not retried and not acked late, so a task runs at most once per
submission; a resubmission is a new job. `JobStore.save_outputs` refuses a job folder that already
holds outputs, so a duplicate delivery cannot mix two runs. Deletes answer `404` the second time,
by the spec.

### Anti-patterns
| Don't | Do instead | Why |
|---|---|---|
| Sort output files by matching the library's file names | Generate each format into its own folder (D-3) | File names are the library's to change |
| Read Celery's result backend for a job's state | Read `meta.json` (D-5) | One source of truth; results expire |
| Pass `run.failures` objects past the adapter | Turn them into strings in `LibraryFingerprinter` | Keeps the domain free of the library |
| Call Celery, Fuseki or the library from a handler | Go through a service and its port | `package-boundaries` |
| Re-render or patch `main.html` | Report the problem to the library | The strict rule |
| Mock `requests` in adapter tests | Test adapters against containers | Mocks of HTTP prove nothing about Fuseki |

## Error matrix

No monitoring is in scope, so no condition raises an alert; the logs are the record. UI messages
are shown as a flash message on the page that made the request.

| Failure mode | Detected by | Handling | Log | UI message |
|---|---|---|---|---|
| Endpoint URL invalid | `InvalidSource` in `submit_endpoint_job` | `400`; no job | info | "Enter an http or https SPARQL endpoint URL." |
| Unsupported upload | `UnsupportedFileType` in `submit_file_job` | `415` listing the types; no job | info | "This file type is not supported. Accepted: …" |
| Redis down when submitting | `send_task` raises | record `failed`, upload discarded; `503` | error | "The job queue is unavailable. Try again later." |
| Endpoint unreachable | `EndpointUnreachable` | state `failed`, reason from the exception | warning | the job page shows "failed" and the reason |
| Library usage error | `ValueError` from the library | state `failed` with the message | error (a bug here) | the job page shows "failed" and the reason |
| Some measurements failed | `run.failures` not empty | outputs saved; `completed_with_failures` | warning | the job page shows the state and the failures |
| A representation fails to render | raised by `generate_representations` | state `failed`; no outputs kept | error | the job page shows "failed" and the reason |
| Fuseki down or dataset creation fails | non-2xx in `FusekiDatasetStore` | state `failed` with the reason; upload discarded | error | the job page shows "failed" and the reason |
| Dataset deletion fails | non-2xx on delete | state unchanged | warning | none |
| Job cancelled | `DELETE /tasks/{id}` | record `cancelled`, task revoked, outputs and upload discarded by `cancel_job`; a running file job's dataset removed by its task (see *Cancel*) | info | "Job cancelled." |
| Cancel of a finished job | state not `queued`/`running` | `409` | info | "This job has already finished." |
| Worker lost mid-job | none (no heartbeat) | the record stays `running` | — | the job stays "running"; `shortcut: no stale-job sweep; add one if workers are lost in practice` |
| Unknown job or report id | no `meta.json` | `404` | info | "No such job or report." |
| Unknown format | Connexion's enum validation | `400` | info | not reachable from the UI |
| Format with no file | `FormatNotAvailable` | `404` | info | the link is not shown |
| Missing secret key | `Settings.from_env()` | the process does not start; the message names the variable | critical | — |

### Stage-1 review (five lenses, 2026-11-08): accepted fixes

Recorded before the fixes (Rule of Divergence):

- **R1-1** TriX uploads: the upload now sends the raw file (Graph Store Protocol), so `Content-Type`
  alone picks Fuseki's parser; `application/xml` is refused (400, checked against
  `stain/jena-fuseki:4.0.0`). `config.INPUT_MIME_TYPES` maps `trix` to `application/trix+xml`; it is
  the one table, read by the one lookup (`adapters.helpers.get_file_format`). Any 2xx answer to an
  upload is a success.
- **R1-2** Secrets: `config.py` no longer logs the Fuseki password or the secret keys;
  `.dockerignore` keeps `.env` files, `db/`, `reports/`, `logs/` and local tooling out of the images.
- **R1-3** The library's `ProfileRun.failures` are logged as a warning until stage 3 records them in
  the job (DEC-11); the profile file is the named constant `LIBRARY_PROFILE_FILE` (D-15).
- **R1-4** `strtobool` raises on an unknown value, as `distutils` did.
- **R1-5** Logging: the API and UI configure the `fingerprinter` logger from
  `RDF_FINGERPRINTER_LOG_LEVEL` (`fingerprinter/logging_setup.py`); services log through module
  loggers. Stage 2 moves the call into `bootstrap`.
- **R1-6** `bash/` and its Makefile targets go now (DEC-14, from stage 4): the scripts could not run
  on Connexion 3 and pointed at the removed `requirements/`.
- **R1-7** Tests write only to their own temporary folders (an autouse fixture), never to the
  repository's `db/` and `reports/`.

### Stage-2 review (five lenses, 2026-11-08): accepted fixes

Recorded before the fixes (Rule of Divergence). *Leader's choices* are marked.

- **R2-1** *(leader's choice)* An endpoint URL with user info (`https://user:pw@host/…`) is refused
  at the boundary (`InvalidSource`, 400), because records are readable by every client and the
  library redacts user info as secret. Query strings are kept as given (endpoints use them, e.g.
  `default-graph-uri`).
- **R2-2** Uploads are capped: `Settings.max_upload_bytes` (`RDF_FINGERPRINTER_MAX_UPLOAD_MB`,
  default 512); `FileUploadStore.save` counts the bytes it writes and raises `UploadTooLarge`
  (413), discarding the partial file.
- **R2-3** A worker runs a job only from `queued` (a duplicate delivery or a cancelled record is
  logged and left alone); a failed run discards any saved outputs before recording `failed`.
- **R2-4** Only broker errors are `QueueUnavailable` (503): `CeleryJobQueue` translates kombu and
  connection errors; any other exception while queueing propagates as the bug it is.
- **R2-5** `LibraryFingerprinter` reads the profile name from the library's public
  `fingerprint.config.profile_file` (D-15: the service still sets none of the library's variables).
- **R2-6** The `one-library-adapter` contract covers the whole package with one ignored import
  (`fingerprinter.adapters.fingerprint_library -> fingerprint`); `bootstrap` builds the API's and the
  worker's adapters only when those are asked for, so the UI process builds none.
- **R2-7** Feature scenarios run through the API's test client (`create_app` with the fakes), so
  status codes come from the real error handlers and Connexion's validation; the `@unit` scenarios'
  tests carry their scenario names; the in-memory `JobStore` refuses a second save like the real one.
- **R2-8** Clean-up: `job_store=`/`upload_store=`/`dataset_store=` keyword names; `http.HTTPStatus`
  for status codes; the UI's flash categories defined once; the task-state body built by the domain
  (`JobRecord`); `FileJobStore.list` skips a record deleted while listing; one `file_extension`
  helper; the UI quotes path values sent to the API; `uid`/`task_id` are `format: uuid` in the
  contract; `redis_url` is hidden from `repr`; Fuseki errors carry a plain message.

As built: Connexion 3.3 does not validate `format: uuid` on path values, so `uid` and `task_id`
carry a uuid `pattern` (400 on a bad id); a duplicate delivery of a running file job leaves that
job's dataset and upload alone; the UI flashes "The file is too large." on 413.

Deferred, with their home:
- Delete and cancel as `POST` with confirmation: the UI EPIC (`modernise-user-interface` DEC-8).
- Restricting the worker's outgoing traffic (SSRF): stage 4 `infra/` and `SECURITY.md`.
- The Gherkin tightened where stage 2 allowed less ("its seven formats"; failures "in the report's
  metadata"): task 3.4.
- A public one-line failure description in the library: not filed; the adapter's own formatting of
  `Failure` fields is presentation, not a correction.

### As built in stage 2 (task 2.4, 2026-11-08)

- **D-13** The adapter tests use `stain/jena-fuseki:5.1.0`: on 4.0.0, deleting a dataset nobody
  queried answers 500 ("Already closed") although the dataset goes. Task 4.2 pins 5.1.0 in `infra/`.
- **D-15** `LibraryFingerprinter` lets `ValueError` and `EndpointUnreachable` propagate; the job
  service turns any exception into `failed` with its message, so the adapter catches nothing. The
  pitfall scan stays off until task 3.2.
- `FileJobStore` writes `meta.json` through a temporary file and `os.replace` (the API reads while
  the worker writes); `save_outputs` on a job that already holds outputs raises `FileExistsError`.
- The Celery app of `bootstrap` has no result backend, and short publish retries, so a downed Redis
  fails a submission in about a second (task 2.5; measured 0.18 s, a 503 problem response).

### As built in stage 2 (task 2.5, 2026-11-08)

- **D-1** `services/ports.py` also holds `Services`, a frozen dataclass of the ports plus the
  supported upload extensions, and the task names `ENDPOINT_TASK`/`FILE_TASK` shared by the queue
  adapter and the worker. `JobRecord.to_dict()`/`from_dict()` in the domain is the one serialiser of
  the D-4 record, used by `FileJobStore` and the API.
- **D-1, D-8** No `run.py` modules: an entrypoint may not import `bootstrap` (D-16), so the process
  targets are `bootstrap:api_app()` (gunicorn, uvicorn worker), `bootstrap:ui_app()` and
  `bootstrap:celery_app`. `bootstrap` reads `Settings.from_env()` on import, so a missing secret key
  stops every process at start.
- **D-8** `create_app(services, *, swagger_ui)`; the Flask app sets `PROPAGATE_EXCEPTIONS`, so each
  domain exception reaches its own Connexion handler (problem `type` `urn:fingerprinter:<Name>`; 415
  adds `accepted`). Error responses in the OpenAPI file declare no `content`, since Connexion cannot
  pick between `application/json` and `application/problem+json` for one operation.
- **D-7** *Leader's choice:* `RDF_FINGERPRINTER_TIMEZONE` and `TIME_FORMAT` are dropped: job times
  are UTC ISO strings and nothing read them. `RDF_FINGERPRINTER_DEBUG` and the Flask config classes
  went with the `run.py` modules.
- **D-6** No `task_revoked` handler yet: *Risks* makes it conditional on the stage-3 e2e
  cancellation test.

Deferred: action pins by SHA and the deprecated `uvicorn.workers` module (stage 4 images).

## Risks / Trade-offs

- [Connexion 3 is a large migration (ASGI, new test client)] → stage 1 migrates against the old
  contract, before any contract change.
- [Seven formats and the pitfall scan slow every job] → measured in task 3.6 and recorded in the
  durations table (`docs/modules/ROOT/pages/develop/index.adoc#durations`); tuning is a library
  setting, not code here.
- [`revoke(terminate=True)` may kill the worker process before the task's `finally` runs] → the
  e2e cancellation test checks the dataset and upload are gone; if not, cleanup moves to Celery's
  `task_revoked` signal (recorded here first).
- [Stage 1 swaps every dependency at once] → tasks 1.1 to 1.4 are one commit, checked once at its
  end (`tasks.md`).
- [Breaking the API breaks the old UI] → the UI moves with the API in stage 3 (D-9).

## Open Questions

- None blocking. L-1 is settled in task 3.1 under the strict rule.
