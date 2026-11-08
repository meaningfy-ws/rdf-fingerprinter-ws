# EPIC: A modern job console and report viewer

> Golden thread: third EPIC in this repository. Parent: `upgrade-fingerprinter-library` (its
> DEC-5 API contract and DEC-10, which left the UI's look and flows to this EPIC). Seeds:
> `inputs/seed.md` (the developer's answers, 2026-11-08).
>
> **Starts after `upgrade-fingerprinter-library` is archived.** The PLAN (`design.md` + `tasks.md`)
> is derived then, against the delivered API, package layout and `infra/`.

## Appetite

**LARGE**. A new UI over the existing Flask entrypoint, two small API additions (graph listing,
diagram download), one new adapter and one new container (PlantUML). Delivered in three stages,
each one PR into `develop` that leaves `make check-all` and the container tests green.

## Why

After the upgrade a job produces seven outputs, a pitfall scan and a state with failures, but the
UI is a 2020 Materialize page set: a table of three download buttons, a list of raw Celery tasks,
no sign of whether a job is running, finished or failed, and delete and cancel as plain links. A
user cannot see a report without downloading it, nor see the data model at a glance. The
front-end libraries are unmaintained and loaded from CDNs.

## Solution outline

When this EPIC is done, a user opens one console that lists every job with its live state; starts
a job from an endpoint (choosing among the endpoint's named graphs) or from a file; watches it move
from queued to its final state without reloading; and opens a finished job to read its report in
the page, see its class diagram, and download any output or the zip. A failed or partly failed job
says why. Cancelling and deleting ask first.

**Success measure** (judged by the developer at the acceptance demo): on the `infra/` stack from a
clean clone, the developer starts an endpoint job choosing two of its named graphs and a file job,
watches both reach their final state without reloading, reads each report and its class diagram in
the viewer, downloads one format and the zip, sees a job against an unreachable endpoint shown as
failed with its reason, cancels a running job and deletes a report after confirming; the pages pass
an automated WCAG AA check in light and dark themes; the Playwright journeys are green in CI.

Three stages, in this order:

1. **Console.** The new layout and theme, the job list with live state, the two forms, cancel and
   delete with confirmation (DEC-1 to DEC-4, DEC-8).
2. **Viewer and diagrams.** The job page: the report in a sandboxed frame, the class diagram as SVG
   rendered by the worker through the PlantUML container, the downloads (DEC-5 to DEC-7).
3. **Graph picker.** The endpoint form lists the endpoint's named graphs through the library's
   public call (DEC-9). Blocked by `meaningfy-ws/rdf-fingerprinter#63` until it is released.

## Key decisions

- **DEC-1**: Server-rendered Jinja pages with htmx; htmx and the stylesheet are vendored in the
  repository (no CDN, no npm build, no Google Fonts), so the UI works offline and behind a strict
  proxy. Rejected: Next.js (a second stack for a job console; revisit for a fingerprint explorer);
  Tailwind with a node build; keeping Materialize.
- **DEC-2**: The UI stays an HTTP client of the API (the upgrade's D-9 and its import contract): it
  reads job records and files only through the API. Rejected: reading `reports/` directly.
- **DEC-3**: Live state by htmx polling: a job row or job page fragment re-fetches its state every
  few seconds while the job is `queued` or `running`, and stops at a final state. Rejected:
  server-sent events; manual refresh.
- **DEC-4**: One console page lists all jobs (active and finished) with their state; the separate
  "active tasks" page goes. Rejected: keeping two lists.
- **DEC-5**: The report page (`main.html`) is shown in an `iframe` with
  `sandbox="allow-scripts"` (no same-origin), served by the UI from the API's `html` download.
  Pitfall findings are read there. Rejected: rendering profile.json ourselves (report rendering is
  the library's); a plain download link only.
- **DEC-6** *(leader's choice on where)*: The class diagram is rendered by the worker after the
  library writes its PlantUML file, through a `DiagramRenderer` port and a PlantUML-server adapter, and
  stored as `puml/diagram.svg`, so it is in the zip and rendered once. A rendering failure is added
  to the job's failures (`completed_with_failures`); it never fails the job. Rejected: rendering on
  view; rendering in the browser; download only.
- **DEC-7**: A `plantuml/plantuml-server` container in `infra/`, reachable only by the worker,
  with its size limit set for large models; the model never leaves the stack. Rejected: a public
  PlantUML server (it would receive the data model).
- **DEC-8**: A neutral Meaningfy look: system fonts, light and dark themes following the system
  setting, WCAG 2.2 AA (contrast, keyboard use, focus, labels), usable from 360 px wide.
  Destructive actions are `POST` forms behind a confirmation. Rejected: matching another product's
  design system now.
- **DEC-9**: The endpoint form offers the endpoint's named graphs to choose from, listed by the
  library's public call (issue #63) through the `Fingerprinter` port and a new API route; no
  selection means all graphs (the library default). Until #63 is released the form keeps the free
  text field of the console stage. Rejected: free text only; a SPARQL query of our own (a library
  workaround).
- **DEC-10**: UI tests: views and fragments with the Flask test client against a fake API in the
  unit and feature lane; 3 to 5 Playwright journeys against the container stack in CI, with an
  axe-core accessibility check on each page. Rejected: test client only; Playwright for everything.

## Rabbit-holes

- **Large diagrams.** PlantUML refuses or truncates very large images; set
  `PLANTUML_LIMIT_SIZE` and treat a refusal as a listed failure, not a fix in our code.
- **The report frame.** `main.html` is a full page with its own styles and script; do not restyle
  it or inject into it. Size the frame, offer "open in a new tab" and the download.
- **Polling load.** Poll only rows not in a final state, at a fixed interval; no backoff machinery.
- **Playwright in CI.** Browsers and the stack make the job slow; keep the journeys few and run
  them in the container lane only.
- **Accessibility of htmx swaps.** Announce state changes with an `aria-live` region; do not move
  focus on a poll.

## No-gos

- No Next.js, no SPA framework, no node build.
- No fingerprint explorer (classes, properties, search inside `profile.json`): a later EPIC.
- No authentication, users or per-user job lists.
- No new job options (formats, settings, schedules) beyond choosing graphs.
- No changes to the library's report or diagram content; gaps go to the library as issues.
- No SPARQL of our own for listing graphs.

---

## What Changes

- `fingerprinter/entrypoints/ui/`: new templates, layout and theme; htmx and the stylesheet under
  `static/`; the console page with fragments for live state; the job page with the report frame,
  the diagram and the downloads; delete and cancel as `POST` with confirmation; the active-tasks
  page removed.
- `fingerprinter/services/ports.py`: a `DiagramRenderer` port; `Fingerprinter` gains
  `named_graphs(endpoint_url)` (stage 3).
- `fingerprinter/adapters/plantuml.py`: renders PlantUML text to SVG through the PlantUML server.
- `fingerprinter/services/jobs.py`: the worker renders the diagram after the outputs are written.
- API (`openapi/fingerprinter.yml`): format `svg` downloads `puml/diagram.svg`; `GET
  /endpoint-graphs?url=` lists named graphs (stage 3).
- `infra/`: the PlantUML server; its URL in `.env.example`.
- Tests: UI unit and feature tests; Playwright journeys with axe checks in `tests/e2e/`.
- Docs: the UI pages and screenshots in `docs/modules/ROOT/pages/index.adoc`.

## Capabilities

### New Capabilities
- `job-console`: list jobs with their live state, start endpoint and file jobs (with the graph
  picker), cancel and delete with confirmation.
- `report-viewer`: show a job's report, class diagram, failures and downloads.
- `class-diagram`: render a job's PlantUML diagram to SVG, keep it with the report and serve it as
  format `svg`.

### Modified Capabilities

## Impact

- Code: `fingerprinter/entrypoints/ui/`, `services/ports.py`, `services/jobs.py`, a new adapter,
  `bootstrap.py`, the OpenAPI contract.
- Systems: one new container (PlantUML server) in `infra/` and CI.
- Library: `meaningfy-ws/rdf-fingerprinter#63` (stage 3 only).
- Users of the API: additive only (format `svg`, `GET /endpoint-graphs`).
