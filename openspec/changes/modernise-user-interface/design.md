# Design: modernise-user-interface

> Derives from: EPIC modernise-user-interface (`proposal.md`, DEC-1 to DEC-11; re-shaped 2026-11-08).
> Inputs: `inputs/ui-analysis.md`, `inputs/mockups.md` (approved). Builds on the code of
> `upgrade-fingerprinter-library` stages 1–3 (merged); "the upgrade's design" below means
> `openspec/changes/upgrade-fingerprinter-library/design.md`.

## Context

The UI (`fingerprinter/entrypoints/ui/`) is a Flask 3 app, an HTTP client of the API only (import
contract `ui-is-an-api-client`); `bootstrap.ui_app()` builds it. Today: Materialize 1.0 + jQuery +
Google icon fonts from CDNs; pages `/`, `/fingerprint-sparql-endpoint`, `/fingerprint-file`,
`/tasks`, `GET /reports/<id>` (delete), `GET /revoke-task/<id>` (cancel), `/reports/<id>/<format>`
(download, `as_attachment=True`). The API serves the job record (`JobRecord.to_dict`), downloads by
format with `nosniff` (R3-4), job state, and refuses endpoint URLs with user info (R2-1).

## Goals / Non-Goals

Goals: the four approved screens with the approved labels; live status without reload; destructive
actions behind a confirmation and `POST`; the report and diagrams in the page; the graph picker;
WCAG 2.2 AA in light and dark; no external assets. Non-goals: the EPIC's no-gos.

## Decisions

- **U-1 Assets and theme** (DEC-1, DEC-8). `ui/static/app.css`, hand-written; colours as custom
  properties on `:root`, redefined under `@media (prefers-color-scheme: dark)` (no toggle: the
  system setting decides); the colours, badge pairs and copy are in `inputs/mockups.md`, section
  *Copy and colours*; the system font stack; inline SVG icons in `ui/templates/icons.html`;
  `ui/static/vendor/htmx.min.js` = htmx 2.0.4 with its licence file. Materialize, jQuery, Google
  fonts and `main.css` go. Palette as the mockups: accent `#2F5BEA`; status badge pairs (background,
  text) light/dark as in the Jobs mockup, each ≥ 4.5:1.
- **U-2 Labels** (DEC-11). `ui/labels.py` is the only place visible names live: state → label and
  badge class (the table in spec `job-console`); format → name, one-line description and display
  order (Report, Profile (JSON), SHACL shapes, Class diagram (PlantUML), Class diagram (SVG), Pattern
  schema, ShEx schema, Pitfalls (TSV), Download all (.zip)); flash messages ("Job started.",
  "Report deleted.", "Job cancelled."); one sentence per problem `type` (`urn:fingerprinter:<Name>`,
  the Error matrix below), the API's `detail` shown only for a type it does not know. Registered as
  a Jinja global; templates hold no label text of their own except headings and help copy.
- **U-3 States × actions** (rows, Job page and API):

  | State | Filter | Row "Outputs" | Row menu (⋯) | Job page |
  |---|---|---|---|---|
  | `queued`, `running` | In progress | — | Cancel job… | header, status block (polling), "Cancel job…"; no tabs |
  | `completed`, `completed_with_failures` | Finished | Open report · Download all (.zip) | Delete… | header, warnings panel (if any), tabs Report · Class diagram · Downloads, "Delete…" |
  | `failed`, `cancelled` | Failed or cancelled | — | Delete… | header with the reason (failed) or "Cancelled", "Delete…"; no tabs |

  "All" shows every job. The four filters are disjoint and cover every state. Delete is offered
  only for final states; the API refuses to delete an active job (`409` `JobIsActive`, new domain
  exception, `services.reports.delete_report` checks the state first). Cancel is offered only for
  active states (the API already answers `409` otherwise). The row menu is a `<details>` disclosure
  with links to the confirmation pages, so it needs no JavaScript.
- **U-4 UI routes.** The old routes go.

  | Route | Does |
  |---|---|
  | `GET /` | Jobs page; `?show=all|active|finished|stopped` (default `all`; labels All · In progress · Finished · Failed or cancelled) |
  | `GET /jobs/rows?show=&was=<ids>` | the `<tbody>` fragment (htmx). It carries `hx-get` with `hx-trigger="every 3s"` only while a shown job is active, and `hx-vals` with the ids active now as `was` |
  | `GET /jobs/new?from=endpoint|file` | New job page (the tab from the query; no JS needed) |
  | `POST /jobs/endpoint`, `POST /jobs/file` | start a job (CSRF), redirect to `/` with "Job started." |
  | `GET /jobs/<id>?tab=report|diagram|downloads&diagram=<file>` | Job page; a missing or unknown `tab` opens Report |
  | `GET /jobs/<id>/state` | the status block fragment, polling every 3 s while active; once final it answers `HX-Refresh: true` |
  | `GET /jobs/<id>/report` | the API's `html` file, inline, with `Content-Security-Policy: sandbox allow-scripts` and `X-Content-Type-Options: nosniff` (DEC-5); an API `404` gives the UI's "No such job or report." page with status 404 |
  | `GET /jobs/<id>/files/<format>` and `GET /jobs/<id>/files/<format>/<file>` | a download (a whole format, or one listed file of it): always `Content-Disposition: attachment` (name kept from the API), `nosniff` |
  | `GET /jobs/<id>/diagrams/<file>` | one SVG for `<img>`: inline, only for a file of format `svg` listed in the record, with `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; sandbox` and `nosniff` |
  | `GET /jobs/<id>/delete?next=`, `POST /jobs/<id>/delete` | the confirmation page, then the delete (CSRF); redirects to `/` |
  | `GET /jobs/<id>/cancel?next=`, `POST /jobs/<id>/cancel` | the same for cancelling; redirects to `next` (a local path: `/` or `/jobs/<id>`; anything else becomes `/`) |
  | `GET /jobs/new/graphs?url=` | stage 3: the checkboxes fragment, or the sentence why the graphs could not be listed |

  The confirmation is a page drawn as the mockup's dialog over a dimmed page (`role=alertdialog`,
  "Keep it" focused first; "Keep it" links back to `next`). After a `POST`, the outcome is a flash
  on the page redirected to (the Error matrix sentence, or "Report deleted." / "Job cancelled.").
  "Open report" in a row points to `/jobs/<id>/report` (new tab) in stage 1 and to the Job page
  (`/jobs/<id>`) from stage 2. Jobs are listed newest first: the UI sorts the API's list by
  `created_at`, descending.
- **U-5 Announcements.** The page has one `<div id="announce" aria-live="polite">`. The rows fragment
  sends, as an htmx out-of-band swap (`hx-swap-oob="true"`), that region's new text: for each id in
  `was` (comma-separated job ids) whose job is now final, "<source>: <label>." with the full source as listed (e.g. "treaties-source-ap.rdf: Done."); empty
  when nothing ended. A poll that changes nothing announces nothing; focus never moves.
- **U-6 Time.** Rendered in Python from the record's UTC time, in the server's time zone (`TZ`), in a
  `<time datetime="<ISO>" title="<8 Nov 2026, 14:21>">`: under 1 min, or a time in the future
  (clock skew), "just now"; under 60 min "<n> min ago" (whole minutes, rounded down); same day "Today, HH:MM"; previous day "Yesterday, HH:MM"; else "8 Nov 2026,
  HH:MM". Duration "took <s> s" (one decimal under 60 s, else "<m> min <s> s" in whole seconds) from
  `finished_at − created_at`; omitted when `finished_at` is missing.
- **U-7 The job record** (API, additive). `finished_at` (UTC ISO, or `null`) is stamped by the job
  store whenever `set_state` records a final state (so `_finish`, `cancel_job` and
  `_fail_submission` need no change): `FileJobStore` and the in-memory fake take a `clock: Callable[[],
  datetime]` (default `datetime.now(UTC)`), which tests fix. `discard_outputs` also resets `files`.
  The OpenAPI `JobRecord` schema gains `finished_at` and `files`. `files`:
  `{format: [file names]}`, written by `FileJobStore.save_outputs` from the outcome (zip omitted).
  `JobRecord.from_dict` reads both with defaults (`None`, `{}`), so older `meta.json` files still
  load. `GET /reports/{uid}/{format}/{file}`: the file must be listed in `files[format]` (else `404`
  `FormatNotAvailable`); never a path join of the raw name. The UI's file form gets the accepted
  extensions and the upload limit from `bootstrap` (`Settings.INPUT_MIME_TYPES` keys,
  `max_upload_bytes`), passed to `ui.create_app`; no new API route. The UI sets Flask's
  `MAX_CONTENT_LENGTH` to the limit plus 1 MB for the form, and its 413 handler renders the file
  form with the 413 sentence, so a too-large upload never reaches the API.
  The UI's `ApiClient` gains `get_job(id)`, `get_file(id, format, file=None)` (replacing
  `get_report`) and (stage 3) `list_graphs(url)`; `get_active_tasks` goes (no caller is left); the
  other calls keep their routes.
- **U-8 Diagrams** (stage 2, DEC-6). Port `DiagramRenderer.render(puml_text: str) -> bytes`;
  `Services` gains `diagram_renderer`; `run_endpoint_job` and `run_file_job` take it as a keyword
  argument and pass it to `_run`; `entrypoints/worker/tasks.py` passes `services.diagram_renderer`.
  In `services.jobs._run`, after the library run and before `save_outputs`, a function
  `_with_diagrams(outcome, renderer, work_folder) -> FingerprintOutcome` returns the outcome rebuilt
  with the `svg` files and the extra failures: every file of the outcome's
  `puml` format is rendered to `<stem>.svg` in the work folder; the SVGs form format `svg`. A
  renderer error (unreachable, timeout, non-2xx, or a body that is not SVG) adds the failure
  "Class diagram <stem> could not be drawn: <cause>" (logged as a warning) and the job ends
  `completed_with_failures`; the other diagrams and outputs stay. Oversized diagrams are cropped by
  PlantUML, not failed (`PLANTUML_LIMIT_SIZE=16384`). `ReportFormat.SVG = "svg"`, the OpenAPI
  `format` enum, `OUTPUT_MIME_TYPES["svg"] = "image/svg+xml"`, and `labels.py` gain it in task 2.2.
  The Job page's picker. The library names files `diagram-<slug>.puml` (whole model of a graph) and
  `diagram-<slug>--<name>.puml` (one vocabulary of it). Whole-model diagrams come first, then
  vocabulary diagrams, each group alphabetical. Labels: with one graph, "Whole model" and
  "Vocabulary: <name>"; with several, "Whole model — <slug>" and "Vocabulary: <name> — <slug>".
  No `?diagram=`, or one not in the record: the first diagram is shown (an unknown name adds the
  flash "That diagram does not exist."); a `<form method="get">` with a `<select
  name="diagram">` and a "Show" button (htmx submits on change). No `svg` files: "No diagram is
  available." plus the job's failures.
- **U-9 PlantUML** (stage 2, DEC-7). `tests/containers.py` gains a `plantuml` fixture (same image)
  and the e2e `stack` sets `RDF_FINGERPRINTER_PLANTUML_LOCATION`/`_PORT` to it. `adapters/plantuml.py` `PlantUmlRenderer` posts the text to
  `{plantuml_url}/svg` with a 30 s timeout; an answer is SVG when it is 2xx and its body, stripped, starts
  with `<svg` or with an XML declaration followed by `<svg`. Settings `RDF_FINGERPRINTER_PLANTUML_LOCATION` (default
  `http://plantuml`), `_PORT` (`8080`). `docker/docker-compose.yml` gains `plantuml` from
  `plantuml/plantuml-server:jetty-v1.2024.7`, `PLANTUML_LIMIT_SIZE=16384`, no published port. The
  container fixture uses the same image.
- **U-10 Graph listing** (stage 3, DEC-9). `Fingerprinter.named_graphs(url) -> tuple[str, ...]`:
  the adapter calls `list_named_graphs(url, resolve_settings(env={}, config={"timeout_seconds": 20}))`
  and turns `EndpointUnreachable`, `QueryTimeout`, `PermanentError` and `ValueError` (`UsageError`)
  into `GraphListingFailed(reason)` (domain). `services.jobs.list_graphs(url, *, fingerprinter)`
  checks the URL with the same function `submit_endpoint_job` uses (`_check_endpoint_url`, extracted:
  http/https, a host, no user info → `InvalidSource`). `GET /endpoint-graphs?url=` → `200
  {"graphs": [...]}`, `400` `InvalidSource`, `502` `GraphListingFailed` (added to `PROBLEM_STATUS`).
  The UI calls it with a 60 s timeout (the library's 20 s per query, with its retries).
- **U-11 Report frame** (DEC-5). `<iframe src="/jobs/<id>/report" sandbox="allow-scripts"
  title="Report for <source>">` (80vh), plus "Open in a new tab" (same route, so the CSP sandbox
  applies there too). The UI never alters the page.
- **U-12 Tests** (DEC-10). Startup order for the e2e servers: pick the API's free port, set
  `RDF_FINGERPRINTER_API_LOCATION`/`_PORT` (and the PlantUML settings in stage 2), then import
  `bootstrap`; browser fixtures are written by hand with `playwright.sync_api` (no
  `pytest-playwright`). Unit tests with the Flask test client and BeautifulSoup against a fake
  API client (`tests/unit/ui/`), one per spec scenario, named after it. Playwright journeys
  (`tests/e2e/ui/`, marker `e2e`): the e2e stack gains real servers — the API (Connexion ASGI) under
  uvicorn in a thread on a free port, the UI under werkzeug `make_server` in a thread — with the
  existing worker, Fuseki 5.1.0 (a dataset holding `continents-source-ap.rdf`) and Redis.
  `playwright==1.49.1` in the test group; `tests/e2e/ui/axe.min.js` = axe-core 4.10.2 (vendored,
  licence beside it), injected per page and run with the `wcag2a`, `wcag2aa`, `wcag21aa`, `wcag22aa`
  tags; each page checked with `color_scheme` `light` and `dark`, and at a 360 px wide viewport
  (no horizontal scroll of the page); a keyboard-only journey (Tab to "New job", fill the endpoint,
  submit with Enter, reach the new row). CI gains a `containers` job in this EPIC (task 1.0): `make
  install`, `uv run playwright install --with-deps chromium`, `make test-containers`; upgrade task
  4.3 then only adds the release workflow.

## As built in stage 1 (tasks 1.3–1.5, 2026-11-08)

- **U-5** The announcement is an out-of-band swap of the live region's *content*
  (`hx-swap-oob="innerHTML"` on `#announce`): replacing the element itself is not reliably read out.
- **U-4** `next` accepts any local path (so a row's cancel returns to `/?show=active`); `//host`,
  backslashes, schemes and relative paths become `/`.
- **U-4** The confirmation sits in a dimmed content area under the header, not a fixed overlay, so no
  focusable link is hidden behind it (WCAG 2.2 *focus not obscured*).
- **U-2** "What you get" hides "Class diagram (SVG)" until task 2.2 produces it.
- The UI's downloads are proxied into memory, as before (no streaming of large zips).

## Stage-1 review (five lenses, 2026-11-08): accepted fixes

Recorded before the fixes (Rule of Divergence).

- **S1-1** `next` is accepted only when it has no control character or whitespace, no scheme and no
  host, and passes the `//`, `/\` check (an open redirect through `/%09/evil.example` was shown).
- **S1-2** Every UI response sends `X-Frame-Options: SAMEORIGIN` and `Content-Security-Policy:
  frame-ancestors 'self'` (clickjacking of the confirmations); an expired CSRF token renders the form
  again with "This form expired. Please try again."; the session cookie is `SameSite=Lax`, and
  `Secure` when `RDF_FINGERPRINTER_UI_SECURE_COOKIES` is true.
- **S1-3** File downloads are streamed from the API (`stream=True`, passed through).
- **S1-4** `ApiClient` turns API errors into one `ApiError(problem, status)` (in `ui/exceptions.py`)
  and returns parsed values; views call typed methods (no method names as strings, no `requests` in
  views). The job JSON is parsed once into a frozen `ApiJob` with defaults and an unknown-state
  fallback (shown as its raw state with a neutral badge), so one odd record cannot break the page.
- **S1-5** One copy of the rules: `JobRecord.with_state(..., now)` stamps `finished_at`;
  `FingerprintOutcome.file_names` gives the sorted names; `formats` is derived from `files`; the
  "only listed files" check lives in `services.reports.report_download`; both stores use them.
- **S1-6** The UI's format ids, tab ids and config keys are constants (a UI-local `ApiState`
  `StrEnum`, `labels` constants, a `listed_from_stage` flag instead of `!= 'svg'`); button and
  empty-state copy and the form field labels move to `labels.py`; `helpers.py` is folded in;
  `api_wrapper.py` becomes `api_client.py`; one megabyte constant; unused icons and the
  not-yet-existing `GraphListingFailed` sentence removed (it comes with stage 3); a test pins
  `labels.PROBLEMS` to the API's `PROBLEM_STATUS` and the UI's state sets to the OpenAPI enum.
- **S1-7** A 404 after a delete or cancel `POST` lands on `/`; a poll treats only an unreachable API
  (no answer) as "paused" — an error answer shows the server-error sentence in that row.
- **S1-8** Tests: "An endpoint job is started" asserts the new row; the e2e journey asserts the
  announcement once and that no `/jobs/rows` request follows "Done"; the `hx-vals` after a change;
  the `TZ` fixture restores `time.tzset()`.

As built (S1 fixes): `next` checks, framing headers, CSRF expiry and cookies as listed;
`RDF_FINGERPRINTER_UI_SECURE_COOKIES` (default false) added to the settings and `docker/.env`; an
unknown state shows its raw text with a neutral badge; a record written before `files` existed gets
its `files` from its format folders when `FileJobStore` reads it, so older jobs keep their outputs;
the e2e journey cancels leftover active jobs first (`quiet_console`), since the job store outlives a
test module's worker.

## As built in stage 2 (tasks 2.1–2.2, 2026-11-08)

- **U-9** `DiagramRenderer.render` raises `DiagramRenderFailed` (domain); its message is the cause in
  plain words ("the PlantUML server is not reachable", "did not answer in time", "answered <status>",
  "did not answer with an SVG") and never the server's address, since failures are shown to clients.
- **U-8** SVGs are written to `<work folder>/svg/<stem>.svg`; the `svg` format exists only when at
  least one diagram was drawn. The library writes seven formats; the record lists eight once the
  worker has drawn diagrams (the report-access feature step counts the library's seven).

## As built in stage 2 (tasks 2.3–2.4, 2026-11-08)

- **U-3** The Job page's status block shows the state's note only while the job is active.
- **U-8** The picker swaps only the diagram and its download (`hx-select` on `#diagram-view`), so
  keyboard focus stays in the select; the image sits in a scrollable region at natural size.
- **U-4** "Delete…" from the Job page passes `next=/jobs/<id>` ("Keep it" returns there); the
  delete itself lands on `/`.
- The report frame's own content is not checked by axe: it is the library's page, shown unchanged.

## Stage-2 review (five lenses, 2026-11-08): accepted fixes

Recorded before the fixes (Rule of Divergence).

- **S2-1** The PlantUML server runs with `PLANTUML_SECURITY_PROFILE=SANDBOX` (compose and the test
  fixture), so no diagram can make it fetch a URL; the image, its limit and its profile are one set of
  constants in `tests/containers.py`, each with a note naming `docker/docker-compose.yml`.
- **S2-2** Drawing: once the server is unreachable or times out, the job's remaining diagrams are
  recorded as failures without waiting on each; a PlantUML file that cannot be decoded is that
  diagram's failure, not the job's. The failure names the diagram by the label the UI would show
  ("Class diagram (Whole model) could not be drawn: …"), not the file stem; the warning is logged.
- **S2-3** Library dependency L-1 below: the picker depends on the library's diagram file names; an
  integration test runs the real library and asserts `diagram_choices` can label every PlantUML file
  it wrote, so a renamed scheme fails a gate. A split module (`<name>~<n>`) is labelled
  "Vocabulary: <name> (part <n>)".
- **S2-4** The status block answers `HX-Refresh: true` on a 404 (the job is gone), so the reload shows
  "No such job or report."; the tab context (and its flash) is built only for jobs with outputs.
- **S2-5** Copy left in templates moves to `labels.py` (column headers, meta labels, the frame title,
  the image alt); the query names `tab` and `diagram` are constants; the three file routes share one
  helper; the job view is built once per request; the failures list is one macro; the Report tab is an
  include; `Download` separates the file name from the file count; diagrams are a named tuple with an
  explicit sort key; `".svg"` comes from `ReportFormat.SVG`.
- **S2-6** Tests: "The PlantUML server is down" keeps all seven library formats; the e2e journey
  asserts the report frame shows the library's pitfalls section; the warning is logged; the UI
  fixture uses the worker's real failure text.

### Library dependencies

- **L-1** rdf-fingerprinter publishes no description of each diagram file (graph, overview or module,
  part): `meaningfy-ws/rdf-fingerprinter#75`. Until it does, the UI reads the file names
  (`diagram-<slug>.puml`, `diagram-<slug>--<module>.puml`), pinned by the S2-3 integration test. When
  #75 is released, the picker uses the published description and the parsing goes.

## Algorithm — live status

The rows fragment is the same template as the page's table body (`templates/jobs/_rows.html`).
While at least one shown job is active, the `<tbody>` carries `hx-get="/jobs/rows?show=<f>"
hx-trigger="every 3s" hx-swap="outerHTML" hx-vals='{"was": "<active ids>"}'`; otherwise none of
these, so polling stops with the last swap. If the API is unreachable during a poll, the fragment
answers `200` with a `<tbody>` holding only one row "Status updates paused: the service is not
reachable.", carrying the same trigger and the request's `was`, so polling resumes when the API is back. The Job page's
status block does the same and answers `HX-Refresh: true` once the job is final.

## Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Restyle, inject into or re-render the library's `main.html` | Show it in the sandboxed frame as is | Report rendering is the library's (no workarounds) |
| Serve the report or an SVG inline without the CSP sandbox | The U-4 headers per route | Library output carries text from the profiled data |
| Write state names or format ids in templates | `labels.py` | One place for copy (DEC-11) |
| Poll from custom JavaScript or `setInterval` | htmx triggers rendered by the server | One mechanism; stops by itself |
| Match failures by the library's raw text in the UI | Show the record's failures as given; count them | The UI cannot know the library's phrasing |
| Join a requested file name onto a folder | Look it up in the record's `files` | Path traversal |
| Add a CDN, a web font or an npm build | Vendored htmx, system fonts | DEC-1 |

## Error matrix (UI)

Sentences live in `labels.py`; the upgrade's design, section *Error matrix*, is the API side.

| Condition | Where | UI |
|---|---|---|
| API unreachable on a page | any page | the page renders with "The service is not reachable. Try again in a moment." |
| API unreachable during a poll | rows, status block | "Status updates paused: the service is not reachable."; polling continues |
| 400 `InvalidSource` | endpoint form | the URL kept; "Enter an http or https SPARQL endpoint URL, without a user name or password." next to it |
| 413 `UploadTooLarge` | file form | "The file is too large (limit <n> MB)." with `n` from `max_upload_bytes` |
| 415 `UnsupportedFileType` | file form | "This file type is not supported. Accepted: <extensions>." |
| 503 `QueueUnavailable` | either form | "The job queue is unavailable. Try again later." |
| 404 `JobNotFound`/`FormatNotAvailable` | Job page, downloads, report frame, delete/cancel `POST` | "No such job or report." (a flash on `/` after a `POST`) |
| 409 `JobNotCancellable` | cancel | "This job has already finished." (flash on the `next` page) |
| 409 `JobIsActive` | delete | "Cancel the job before deleting it." (flash on `/`) |
| 413 from the UI's own limit | file form | the 413 sentence, with the file field |
| 502 `GraphListingFailed` | "Load graphs" | "Could not list the graphs: <reason>." The form still submits without graphs |
| PlantUML down or failing | worker | the job's failure "Class diagram <stem> could not be drawn: <cause>"; log warning |
| An unknown problem type | any | the API's `detail` |
| A 5xx without a problem body | any | "Something went wrong on the server. Try again." |

## Risks / Trade-offs

- **Playwright in CI** is slow and downloads a browser: only in the container job.
- **Cropped diagrams** above 16384 px: accepted; the PlantUML file is still downloadable.
- **Polling load**: 3 s per open page, only while something is active.

## Open Questions

None.
