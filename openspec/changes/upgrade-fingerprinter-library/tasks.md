> Derives from: EPIC `upgrade-fingerprinter-library` (`proposal.md`); design `design.md` (D-1 to D-17, L-1).

Each stage ends in one PR into `develop`, run through the stage loop of
`docs/modules/ROOT/pages/develop/agents.adoc#stage-loop`. Tasks 1.1 to 1.4 land as **one commit**
(the dependency swap cannot be green halfway) and end with `uv run pytest` green; every task from
1.5 on leaves `uv run pytest` green, and from 1.6 on `make check-all` green. Evidence goes in
`openspec/changes/upgrade-fingerprinter-library/evidence/`; durations go in the table at
`docs/modules/ROOT/pages/develop/index.adoc#durations`. Reference repository for tooling files:
`/home/lps/work/repos/rdf-persistence` (named files are copied and adapted, not invented).

## 1. Stage 1 — Foundation (DEC-6, DEC-7, DEC-9, D-10, D-14)

- [x] 1.1 Add `pyproject.toml` (uv build backend with `module-root = ""`, `requires-python >=3.12,<3.15`, groups `test`/`lint`/`dev`, exact pins per D-10), `.python-version` (`3.13`) and `uv.lock`; remove `requirements/`, `requirements.txt` and `setup.cfg`. Check: `uv sync` succeeds on 3.13.
- [x] 1.2 Remove the imports of dropped packages (D-10): `selenium` in `tests/conftest.py`, and any `SPARQLWrapper`, `eds4jinja2`, `rdflib`, `requests_toolbelt`, `shortuuid`, `click` import left unused. Check: `grep -rn` finds none, and `uv sync` still succeeds.
- [x] 1.3 Replace both `generate_endpoint_fingerprint_report` calls in `fingerprinter/services/report_handling.py` with one `fingerprint_report(..., formats=(), prefix_list=None)` built with `resolve_settings(env={}, selected_graphs=graphs)` (D-14, D-15); serve `main.html` as `html`, `profile.json` as `json`, their zip as `zip`. Remove `resources/templates/`, the template settings in `fingerprinter/config.py`, `logging.conf` when nothing reads it, and `make set-report-template`. Unit tests updated first.
- [x] 1.4 Migrate the API to Connexion 3 (`FlaskApp`, uvicorn worker, D-8) and the UI to Flask 3, keeping today's routes and contract; adapt the test clients. Check: every existing test passes with `uv run pytest`. Commit 1.1–1.4 together.
- [x] 1.5 Move the tests into `tests/unit/` and `tests/feature/` and add the marker hook of `/home/lps/work/repos/rdf-persistence/tests/conftest.py` to `tests/conftest.py` (D-11); add `pytest.ini` from `/home/lps/work/repos/rdf-persistence/pytest.ini` (no coverage flags).
- [x] 1.6 Add `ruff.toml`, `mypy.ini`, `.coveragerc` (D-12), `.pre-commit-config.yaml` from the reference repository's files, and `.importlinter` with one stage-1 contract (`fingerprinter.services` and `fingerprinter.adapters` do not import `fingerprinter.entrypoints`, which today's code meets). Add the Makefile targets of `/home/lps/work/repos/rdf-persistence/Makefile`: `install`, `lock`, `format`, `lint`, `lint-fix`, `typecheck`, `check-architecture`, `check-spec`, `test`, `test-unit`, `test-feature`, `check-quality` (= `lint typecheck check-architecture check-spec check-docs`; the reference's generation and freshness targets do not apply), `check-all`; remove the pip targets. Fix the Ruff and mypy findings in their own commits.
- [x] 1.7 Raise the unit and feature lane to ≥ 80 % coverage, test-first on the code stage 2 keeps (the API handlers and helpers, the UI views and forms). Check: `make check-all` green.
- [ ] 1.8 Replace `.github/workflows/tests.yml` with `.github/workflows/ci.yml`: Python 3.13, `astral-sh/setup-uv`, Node 20 (for `make check-spec`'s `npx`), `make install` and `make check-all` on PRs into and pushes to `develop`; remove Codecov.
- [ ] 1.9 Stage 1 PR into `develop` (stage loop; no use case changes, so no acceptance demo).

## 2. Stage 2 — Structure (DEC-8, D-1, D-2, D-5, D-6, D-7, D-16)

- [ ] 2.1 Write `tests/feature/fingerprinting_jobs.feature` and `tests/feature/report_access.feature` from the spec scenarios (one Gherkin scenario per spec scenario, same name) and get the developer's sign-off.
- [ ] 2.2 `fingerprinter/domain/model.py` and `fingerprinter/domain/exceptions.py` (D-1), test-first.
- [ ] 2.3 `fingerprinter/services/ports.py` (D-2) with in-memory fakes in `tests/fakes.py`; `fingerprinter/services/jobs.py` and `fingerprinter/services/reports.py` (the algorithm of `design.md`), test-first through the fakes; the feature steps for the scenarios the test map marks *feature*.
- [ ] 2.4 Adapters `fuseki.py`, `file_job_store.py` (D-3, D-5), `file_upload_store.py`, `celery_queue.py` (D-6), `fingerprint_library.py` (stage-1 outputs: `html` and `json` only); integration tests in `tests/integration/` against Fuseki (`stain/jena-fuseki`) and Redis containers through testcontainers; add `make test-containers` (no coverage floor, D-12).
- [ ] 2.5 `fingerprinter/config.py` `Settings.from_env()` (D-7), `fingerprinter/bootstrap.py` (D-1, D-6), `fingerprinter/entrypoints/worker/tasks.py`; the API handlers call the services from `flask.current_app.extensions["fingerprinter"]` (D-8); the UI stays an HTTP client and gets its settings from `bootstrap.ui_app()` (D-9). The routes of D-17 serve the job record; the UI's job page shows its state, reason and failures. Delete `fingerprinter/adapters/{celery,sparql_adapter,helpers}.py` and `fingerprinter/services/{report_handling,handlers,db,file,tasks,time}.py` and their tests once replaced.
- [ ] 2.6 Replace the stage-1 `.importlinter` with the contracts of D-16; add `tests/unit/test_architecture.py`, which runs `lint-imports` on a temporary copy of the package with one forbidden import per `package-boundaries` scenario and expects a failure naming it.
- [ ] 2.7 Stage 2 PR into `develop` (stage loop; the PR notes the API break of D-17; no new use case, so no acceptance demo).

## 3. Stage 3 — Outputs and API (DEC-1 to DEC-5, DEC-10, DEC-11, DEC-15, D-3, D-4, D-9, L-1)

- [ ] 3.1 Settle L-1: in `tests/integration/test_fingerprint_library.py`, render `pattern`, `shex` and `pitfalls` with `generate_representations` from a profile of `tests/resources/continents-source-ap.rdf`. If all render, the leader files the `documentation` issue; if one fails, stop and file a `bug` issue (strict rule).
- [ ] 3.2 Add `tests/resources/pitfall-untyped-class.ttl`, a small graph that makes the packaged check `p34_untyped_class` report at least one finding when scanned as the default graph (if `p34` does not run on a default graph without schema graphs, choose another packaged check that does, and name it in the commit). `LibraryFingerprinter`: pitfall scan on, the seven formats in their folders (D-3), failures as strings; integration tests per the test map.
- [ ] 3.3 `FileJobStore`: per-format files, multi-file formats zipped on download, `report.zip`, the job record; unit tests per the test map.
- [ ] 3.4 The OpenAPI contract and handlers of D-4 (routes, `202`, the job record, problem responses per the error matrix); feature tests per the test map, with the fake `Fingerprinter` returning failures for "Failed measurements are listed".
- [ ] 3.5 UI: the report and job pages show the state, reason and failures and one link per available format; the download route proxies `GET /reports/{uid}/{format}`; flash messages per the error matrix's UI column; unit tests with BeautifulSoup per the test map.
- [ ] 3.6 E2E tests in `tests/e2e/` (the API app, a real worker, Fuseki, Redis) per the test map; record each job's duration in the durations table.
- [ ] 3.7 Stage 3 PR into `develop`, with the acceptance demo of an endpoint job and a file job, from the API and the UI, recorded in `evidence/acceptance-stage-3.md`.

## 4. Stage 4 — Infrastructure and delivery (DEC-12, DEC-13, DEC-14, D-13)

- [ ] 4.1 `infra/`: multistage non-root Dockerfiles (`api`, `ui`, `worker`) on Python 3.13 with uv; `infra/compose.yaml` (api, ui, worker, flower, redis, fuseki) without source mounts; `infra/.env.example` with placeholders and none of the library's operational variables (D-15, `tests/unit/test_infra_env.py`); `infra/.env` git-ignored. Remove `docker/`, `bash/` and their Makefile targets; add `make up`, `down`, `rebuild`, `logs`, `run-api`, `run-ui`, `run-worker` (the Docker block of `/home/lps/work/repos/rdf-persistence/Makefile`).
- [ ] 4.2 Pick the `stain/jena-fuseki` tag per D-13; pin it in `infra/compose.yaml` and the container fixtures.
- [ ] 4.3 CI: a `containers` job in `ci.yml` running `make test-containers` (integration and e2e); `.github/workflows/release.yml` building the three images and pushing them to `ghcr.io/meaningfy-ws/` on a GitHub release; remove `package.yml`.
- [ ] 4.4 Rewrite `README.md` for uv, `make install`, `make up` and the API of D-4, folding in `curl-examples.md`; update `docs/modules/ROOT/pages/index.adoc`, the runbook's *Tools* and *Before a PR* sections (`docs/modules/ROOT/pages/develop/index.adoc`), `AGENTS.md` *Project specifics* and `openspec/config.yaml` `context:`; add `CHANGELOG.md` and `SECURITY.md`.
- [ ] 4.5 Check the success measure's last clause: `grep -rn` finds no `rdf-fingerprinter~=0.3`, `python 3.8`/`3.8` image or `requirements/` reference outside `openspec/changes/*/inputs/`.
- [ ] 4.6 Stage 4 PR into `develop`, with the acceptance demo of the EPIC's success measure on a clean clone, recorded in `evidence/acceptance-stage-4.md`.
- [ ] 4.7 Archive the change (`openspec archive upgrade-fingerprinter-library --yes`); mark DEC-4 points 4–5 and DEC-6 resolved in `openspec/changes/data-profiling-tool/proposal.md`.

## Test map

Every spec scenario and where it is proven (traceability check, before each stage PR). Fixtures
live in `tests/resources/`.

| Spec · scenario | Tier · file | Fixture / double |
|---|---|---|
| jobs · A valid endpoint is queued | feature · `fingerprinting_jobs.feature` | fake `JobQueue` |
| jobs · An invalid URL is rejected | feature | — |
| jobs · An RDF/XML file is queued | feature | `continents-source-ap.rdf` |
| jobs · An unsupported file is rejected | feature | a `notes.txt` upload |
| jobs · An endpoint job writes all formats | integration · `test_fingerprint_library.py`; e2e · `test_jobs.py` | Fuseki with `continents-source-ap.rdf` |
| jobs · The pitfall findings reach the report page | integration · `test_fingerprint_library.py` | `pitfall-untyped-class.ttl` (task 3.2) |
| jobs · Named graphs are profiled when none is selected | integration · `test_fingerprint_library.py` | Fuseki: `continents-source-ap.rdf` default, `courts-source-ap.rdf` in `http://example.org/g1` |
| jobs · The dataset is removed after success | feature (fakes); e2e · `test_jobs.py` (Fuseki has no `fp-<id>`) | `treaties-source-ap.rdf` |
| jobs · The dataset is removed after failure | feature (fake `Fingerprinter` raising; the fake `DatasetStore` records the delete); integration · `test_fuseki.py` (delete removes a dataset) | fakes; Fuseki |
| jobs · A just-accepted job is queued | feature | fake `JobQueue` (never runs) |
| jobs · An unknown job is not found | feature | — |
| jobs · An unreachable endpoint fails the job | e2e · `test_jobs.py` | `http://unreachable.invalid/sparql` |
| jobs · Failed measurements are listed | feature | fake `Fingerprinter` returning two failures |
| jobs · A running job can be cancelled | e2e · `test_jobs.py` (no `fp-<id>` dataset, no upload, no outputs); feature (a `queued` file job: upload discarded) | a file job cancelled while `running`; fakes |
| jobs · A finished job cannot be cancelled | feature | a `completed` record |
| access · A completed job appears in the list | feature | fake `Fingerprinter` |
| access · A failed job appears without formats | feature | fake `Fingerprinter` raising `JobFailed("endpoint unreachable: http://unreachable.invalid/sparql")` (a test-only exception in `tests/fakes.py`) |
| access · The report page is downloaded | unit · `test_file_job_store.py`; feature | a saved outcome |
| access · A multi-file format is zipped | unit · `test_file_job_store.py` | two `puml` files |
| access · Everything is zipped | unit · `test_file_job_store.py` | seven formats |
| access · An unknown format is rejected | feature (Connexion validation) | — |
| access · An unknown report is not found | feature | — |
| access · A format with no file is not found | unit · `test_file_job_store.py`; feature | an empty `shacl` folder |
| access · A report is deleted | feature | — |
| access · All reports are deleted | feature | two records |
| access · Deleting an unknown report | feature | — |
| access · The report page lists the downloads | unit · `tests/unit/ui/test_views.py` | a fake API answer |
| access · Failures are shown | unit · `tests/unit/ui/test_views.py` | a `completed_with_failures` record |
| boundaries · every scenario | unit · `test_architecture.py`; `make check-architecture` | a temporary package copy |
| (D-15: library operational variables unset) | unit · `tests/unit/test_infra_env.py` fails on any of the eight library variables in `infra/.env.example` (task 4.1) | `infra/.env.example` |

## Roadmap

- [x] 1.1 · [ ] 1.2 · [ ] 1.3 · [ ] 1.4 · [ ] 1.5 · [ ] 1.6 · [ ] 1.7 · [ ] 1.8 · [ ] 1.9
- [ ] 2.1 · [ ] 2.2 · [ ] 2.3 · [ ] 2.4 · [ ] 2.5 · [ ] 2.6 · [ ] 2.7
- [ ] 3.1 · [ ] 3.2 · [ ] 3.3 · [ ] 3.4 · [ ] 3.5 · [ ] 3.6 · [ ] 3.7
- [ ] 4.1 · [ ] 4.2 · [ ] 4.3 · [ ] 4.4 · [ ] 4.5 · [ ] 4.6 · [ ] 4.7

## Verification

`openspec validate upgrade-fingerprinter-library --strict`; the clarity gate (≥ 9/10) on this PLAN;
per stage `make check-all` and, from 2.4, `make test-containers`, green in CI; the test map's
traceability check before each stage PR; the acceptance demos of 3.7 and 4.6.
