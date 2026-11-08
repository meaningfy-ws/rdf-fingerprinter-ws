> Derives from: EPIC modernise-user-interface (`proposal.md`, DEC-1 to DEC-11); design U-1 to U-12.

Each stage is one PR into `develop` through the stage loop
(`docs/modules/ROOT/pages/develop/agents.adoc#stage-loop`), `make check-all` and `make
test-containers` green. Scenario sign-off: the developer approved the mockups that carry these
scenarios and asked to implement them (2026-11-08, `inputs/mockups.md`).

## 1. Console (DEC-1 to DEC-4, DEC-8, DEC-11; U-1 to U-7, U-12)

- [x] 1.0 CI: a `containers` job in `.github/workflows/ci.yml` (`make install`, `uv run playwright install --with-deps chromium`, `make test-containers`) on PRs into and pushes to `develop`; add `playwright==1.49.1` to the test group; note in the upgrade's `tasks.md` 4.3 that the job exists.
- [x] 1.1 U-1 and U-2: `ui/static/app.css`, `ui/static/vendor/htmx.min.js` (2.0.4, with its licence), `ui/templates/icons.html`, `ui/labels.py`, the new `base.html` (header with the mark, "Jobs", "New job"; the `#announce` live region; flash area); Materialize, jQuery, Google fonts and `main.css` removed. Tests in `tests/unit/ui/test_layout.py`: every page references only same-origin scripts, styles and fonts; `labels.py` names every state and format.
- [x] 1.2 U-7 and the API side of U-3: `finished_at` and `files` in the job record with load defaults (`domain/model.py`; the job store's `set_state` stamps it, so `FileJobStore` and the fake change, `services/jobs.py` does not); `GET /reports/{uid}/{format}/{file}` (OpenAPI, handler, record lookup, `404`); `JobIsActive` (`409`) on deleting an active job; `bootstrap` passes the accepted extensions and the upload limit to `ui.create_app`; the job store's `clock` and `finished_at` stamping; `discard_outputs` resets `files`; the OpenAPI `JobRecord` schema. Tests: `tests/unit/domain/test_model.py` (old record loads), `tests/unit/adapters/test_file_job_store.py` (files listed), `tests/unit/services/test_jobs.py` (finished_at per final state), `tests/unit/services/test_reports.py` (active job not deleted), `tests/unit/api/test_api.py` (one file; unknown file `404`; delete active `409`).
- [x] 1.3 U-3 to U-6: the Jobs page and its rows fragment: Source (name + kind line), Started (U-6), Status badge + note, Outputs and the ⋯ menu per the U-3 table; the four filters; newest first; the empty state; polling only while active; announcements (U-5); the paused-updates row. Tests in `tests/unit/ui/test_jobs_page.py` and `tests/unit/ui/test_time.py` (each U-6 threshold). Tests named after the `job-console` scenarios "Jobs in every state are listed", "An empty console says so", "A running job reaches completion", "Finished jobs do not poll".
- [x] 1.4 The New job page: tabs, endpoint form (free-text graphs until 3.2), file form (types and limit from `bootstrap`), "What you get"; `POST /jobs/endpoint`, `POST /jobs/file`; sentences per the Error matrix. Tests in `tests/unit/ui/test_new_job.py`, named after "An endpoint job is started", "An invalid URL is refused", "An unsupported file is refused".
- [x] 1.5 Delete and cancel per U-3: confirmation pages and `POST` routes; downloads through `/jobs/<id>/files/<format>` with the U-4 headers; `/jobs/<id>/report` (U-4 headers; the stage-1 target of "Open report"); the `ApiClient` methods of U-7; the old routes, templates and their tests removed (`/fingerprint-*`, `/tasks`, `/revoke-task/*`, `/reports/*`; `tests/unit/ui/test_views.py` replaced, `test_api_client.py` rewritten). Tests in `tests/unit/ui/test_confirmations.py` (incl. the download headers), named after "A running job is cancelled", "A delete is abandoned", "A finished job offers no cancel".
- [ ] 1.6 U-12: the API and UI server threads on the e2e stack; `tests/e2e/ui/test_journeys.py` ("start an endpoint job and watch it finish" on the continents dataset, "delete with confirmation") and `tests/e2e/ui/test_accessibility.py` ("No external assets", "Both themes pass" on Jobs, New job and the confirmation, each also at 360 px; the keyboard-only journey); CI's container job installs Chromium.
- [ ] 1.7 Stage 1 PR, with the acceptance demo in `evidence/acceptance-stage-1.md`.

## 2. Job page, report and diagrams (DEC-5 to DEC-7; U-4, U-8, U-9, U-11)

- [ ] 2.1 U-9: `DiagramRenderer` port and fake (`tests/fakes.py`); `Services.diagram_renderer`; the `plantuml` container fixture and the e2e stack's PlantUML settings; `adapters/plantuml.py`; settings and `bootstrap`; the PlantUML service in `docker/docker-compose.yml`; container fixture and `tests/integration/test_plantuml.py` (SVG for a small diagram; a non-SVG answer is an error).
- [ ] 2.2 U-8 in the worker (`_with_diagrams`, the renderer passed through `run_*` and the worker tasks): `ReportFormat.SVG`, the OpenAPI enum, `OUTPUT_MIME_TYPES["svg"]`, labels; every PlantUML file rendered to `svg`; a renderer failure is a listed failure, partial failure keeps the drawn ones. Tests named after "A diagram is rendered" and "The PlantUML server is down" in `tests/unit/services/test_jobs.py`, "One diagram is fetched" and "An unknown diagram is not found" in `tests/unit/api/test_api.py`; the e2e endpoint job also asserts `svg` files.
- [ ] 2.3 The Job page per U-3: header (title, badge, meta line with U-6 time and duration, "Delete…"/"Cancel job…"), the warnings panel ("Some parts could not be produced (n)", expandable), tabs Report (U-11 and `/jobs/<id>/report` with its headers), Class diagram (U-8 picker, `/jobs/<id>/diagrams/<file>` with its headers, "Download SVG"), Downloads (U-2 names, descriptions, file counts from `files`); status block polling. Tests in `tests/unit/ui/test_job_page.py`, named after "The report is read in the page", "The diagram is shown", "The diagram failed to render", "Downloads are listed", "An unreachable endpoint".
- [ ] 2.4 `tests/e2e/ui/test_journeys.py`: "open a job's report, diagram and a download"; axe on the Job page in light and dark. Stage 2 PR with `evidence/acceptance-stage-2.md`.

## 3. Graph picker (DEC-9; U-10)

- [ ] 3.1 U-10: `GraphListingFailed`; `Fingerprinter.named_graphs` over `list_named_graphs` (`tests/integration/test_fingerprint_library.py`: two named graphs listed sorted; an unreachable URL gives `GraphListingFailed`); `_check_endpoint_url` shared; `services.jobs.list_graphs` (`tests/unit/services/test_jobs.py`); `GET /endpoint-graphs` (`tests/unit/api/test_api.py`: `200`, `400`, `502`).
- [ ] 3.2 "Load graphs" (`GET /jobs/new/graphs`, htmx; without JS a GET of the New job page with `?url=` lists them) with checkboxes; chosen graphs submitted; the failure sentence. Tests in `tests/unit/ui/test_new_job.py`, named after "Two graphs are chosen", "The endpoint cannot be reached for its graphs".
- [ ] 3.3 Docs: the UI pages and fresh screenshots in `docs/modules/ROOT/pages/index.adoc`. Stage 3 PR with `evidence/acceptance-stage-3.md`; archive the change.

## Test map

| Spec · scenario | Tier · file |
|---|---|
| job-console · Jobs in every state are listed / An empty console says so | unit · `tests/unit/ui/test_jobs_page.py` |
| job-console · A running job reaches completion / Finished jobs do not poll | unit · `tests/unit/ui/test_jobs_page.py`; e2e · `tests/e2e/ui/test_journeys.py` |
| job-console · An endpoint job is started / An invalid URL is refused / An unsupported file is refused | unit · `tests/unit/ui/test_new_job.py` |
| job-console · Two graphs are chosen / The endpoint cannot be reached for its graphs | unit · `tests/unit/ui/test_new_job.py`; integration · `tests/integration/test_fingerprint_library.py` (named_graphs) |
| job-console · A running job is cancelled / A delete is abandoned / A finished job offers no cancel | unit · `tests/unit/ui/test_confirmations.py`; e2e journey (delete) |
| report-viewer · The report is read in the page / The diagram is shown / The diagram failed to render / Downloads are listed / An unreachable endpoint | unit · `tests/unit/ui/test_job_page.py` |
| report-viewer · No external assets / Both themes pass | e2e · `tests/e2e/ui/test_accessibility.py` |
| class-diagram · A diagram is rendered | unit · `tests/unit/services/test_jobs.py` (fake renderer); integration · `tests/integration/test_plantuml.py` (real renderer); e2e · `tests/e2e/test_jobs.py` (svg files) |
| class-diagram · The PlantUML server is down | unit · `tests/unit/services/test_jobs.py` |
| class-diagram · One diagram is fetched / An unknown diagram is not found | unit · `tests/unit/api/test_api.py` |

## Roadmap

- [x] 1.0 · [x] 1.1 · [x] 1.2 · [x] 1.3 · [x] 1.4 · [x] 1.5 · [ ] 1.6 · [ ] 1.7
- [ ] 2.1 · [ ] 2.2 · [ ] 2.3 · [ ] 2.4
- [ ] 3.1 · [ ] 3.2 · [ ] 3.3

## Verification

`openspec validate modernise-user-interface --strict`; the clarity gate (≥ 9/10) on this PLAN;
per stage `make check-all` and `make test-containers` green in CI; the test map's traceability
check before each stage PR; the acceptance demos.
