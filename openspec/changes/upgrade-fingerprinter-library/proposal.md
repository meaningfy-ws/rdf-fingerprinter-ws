# EPIC: Upgrade to rdf-fingerprinter 3 on a modern, standard stack

> Golden thread: second EPIC in this repository; no parent spec yet. Seeds: `inputs/seed.md` (the
> developer's answers, 2026-11-08), `inputs/gap-report.md` (the audit against the Meaningfy standard
> and the library 3.5.0). Unblocks the parked `data-profiling-tool` EPIC (its DEC-4 and DEC-6).
> The UI EPIC follows this one.

## Appetite

**VERY LARGE**. It cuts across the whole repository: the library, the Python version, every
dependency, the package structure, the API contract, the tests, the infrastructure and CI. It is
delivered in four stages, each one PR into `develop` that leaves `make check-all` green.

## Why

The service is pinned to `rdf-fingerprinter` 0.3.1 on Python 3.8 (2022). The library is now at
3.5.0: fast bounded queries, a real JSON profile, prefixed readable reports, SHACL, PlantUML, LLM
schemas and pitfall scans. None of that reaches users, because 0.3.1 cannot run on a Python the
library now supports, and the call the service uses was removed in 3.0. The repository also lacks
every gate the Meaningfy standard expects, so the upgrade cannot be made safely as it stands.

## Solution outline

When this EPIC is done, a user who fingerprints a SPARQL endpoint or an uploaded file, through the
API or the UI, gets everything the library can produce, downloadable one format at a time or as one
zip. A job that ran into trouble says so. The repository runs on Python 3.13 with uv and the
Meaningfy gates, its code is layered (Cosmic Python), and CI proves the behaviour against a real
Fuseki, Redis and Celery worker.

**Success measure** (judged by the developer at the acceptance demo): on the `infra/` stack built
from a clean clone with `make install` and `make up`, fingerprinting one SPARQL endpoint and one
uploaded file, from the UI and from the API, each yields the seven outputs and the zip, each
downloadable; the endpoint job surfaces its pitfall findings in `main.html`; a job against an
unreachable endpoint shows as failed with its reason; `make check-all` and the container tests are
green in CI on Python 3.13; nothing in the repository refers to `rdf-fingerprinter` 0.3, Python 3.8
or `requirements/`.

Four stages, in this order:

1. **Foundation.** uv and a minimal `pyproject.toml` on Python 3.13, every dependency at its current
   release (DEC-6), `rdf-fingerprinter` 3.5 called through `fingerprint_report`, the dedicated tool
   configs and the gates (DEC-9), the tests split into tiers. The service works as before, on the
   library's report.
2. **Structure.** The package reshaped into domain, services with their ports, adapters,
   entrypoints and a composition root, enforced by import-linter (DEC-8).
3. **Outputs and API.** Every format, the pitfall scan, downloads by format, visible failures, and
   the Flask UI adapted to them (DEC-1 to DEC-5, DEC-10, DEC-11).
4. **Infrastructure and delivery.** `infra/`, current images, `.env.example`, the container tests
   in CI, images to GHCR, the release files, the old scripts and docs removed (DEC-12 to DEC-14).

The stages cannot be reordered: 0.3.1 does not install on Python 3.13, so the library swap must land
with the foundation; the structure comes before the new behaviour so the behaviour is built
test-first in its final place.

## Key decisions

- **DEC-1**: A job writes every output the library offers: `main.html`, `profile.json`, SHACL,
  PlantUML, the pattern schema, ShExC and the pitfalls TSV, plus a zip of all of them. Reason: the
  developer wants the library's full value available now. Rejected: parity (HTML, JSON, zip); formats
  as API options.
- **DEC-2**: The pitfall scan runs on every job. Reason: its findings belong in the report the user
  receives. Rejected: off by default.
- **DEC-3**: When no graph is selected, the job profiles the default graph and every named graph
  (the library's default). Reason: follow the library rather than override it. Rejected: the 0.3.1
  behaviour (default graph only).
- **DEC-4**: The custom report templates are dropped: `resources/templates/`, the template volume,
  `make set-report-template` and their settings. The report is the library's. Reason: they cannot
  render the 3.x view model, and report rendering is library work. Rejected: a template hook;
  porting the cellar template.
- **DEC-5**: The API may break, but changes only where the new outputs require it: reports are
  downloaded by format name instead of `html|json|zip`, and a job's state includes its failures. The
  contract stays OpenAPI-first and JSON, ready for the UI EPIC. Rejected: keep it compatible; a full
  `/v2` redesign now.
- **DEC-6**: The same web stack at its current majors: Flask 3, Connexion 3, Flask-WTF, Celery 5.5,
  the current Redis client and Flower. Reason: least change to the architecture, current security
  fixes. Rejected: minimum bumps only; FastAPI (a later decision, if any).
- **DEC-7**: Python 3.13 for the code, CI and images; `requires-python >=3.12,<3.15`. Reason: the
  Meaningfy current version (as MWB2), supported by the library. Rejected: 3.12, 3.14.
- **DEC-8**: Full Cosmic Python: a domain layer, ports in services, adapters behind them, the
  entrypoints (API, UI, Celery worker) and a composition root; import-linter enforces the direction.
  The library is called only from an adapter, through its public API. Reason: the developer's
  choice; it also removes today's import cycle (`adapters/celery.py` ↔ `services`). Rejected: fix the
  cycle only; tooling only.
- **DEC-9**: The full Meaningfy gates from day one, the debt fixed in this EPIC: Ruff, mypy, import-
  linter, coverage ≥ 80 %, all in `make check-all` and CI, configured in dedicated root files as in
  rdf-persistence. Rejected: a coverage ratchet.
- **DEC-10**: The Flask UI keeps working, minimally: on Flask 3, with download links per format and
  a job's failures shown. Its look and flows are the UI EPIC's. Rejected: freezing it.
- **DEC-11** *(leader's choice)*: A job whose report was written with failed measurements ends as
  *completed with failures* and lists them; an unreachable endpoint or a usage error fails the job
  with its reason. Reason: today failures are silent.
- **DEC-12**: Infrastructure moves to `infra/` (compose, `.env.example`, multistage non-root images on
  Python 3.13 with uv); images are published to GHCR on release; Docker Hub publishing is removed.
- **DEC-13**: The committed `.env` files are replaced by `.env.example` with placeholders; `.env` is
  git-ignored; the committed keys are treated as burned. No history rewrite.
- **DEC-14**: `bash/` and its Makefile targets are removed, replaced by `make install`, `make up` /
  `down` and local run targets.
- **DEC-15** *(leader's choice)*: No prefix.cc lookup at run time: the library's packaged prefixes
  apply, so runs are offline and repeatable.
- **DEC-16** *(leader's choice)*: Reports written by the 0.3.1 service are not migrated; there is
  no known deployment.

## Rabbit-holes

- **Connexion 3.** It is ASGI-based with a new app factory, error handling and test client. Keep the
  OpenAPI file as the contract and follow the migration guide; do not redesign the API while
  migrating.
- **Celery under test.** Unit and feature tests run tasks eagerly or behind a fake; only the
  container tests use a real worker and broker.
- **Long jobs.** The pitfall scan and every format make jobs slower. Measure on the test fixtures and
  record it; tuning the library's timeouts or concurrency is a setting, not new code.
- **Fuseki image.** `stain/jena-fuseki` needs `ADMIN_PASSWORD` set and is old; a current image may
  change the admin API paths the dataset adapter uses.
- **Over-modelling the domain.** The domain holds jobs, reports and formats, not a copy of the
  library's profile model.

## No-gos

- No changes to the library from this repository; a gap becomes an issue in
  `meaningfy-ws/rdf-fingerprinter` (`develop/rdf-fingerprinter.adoc`).
- No profiling queries, statistics or report rendering of our own.
- No UI redesign, no new screens, no Next.js: that is the UI EPIC.
- No new API capabilities beyond what DEC-5 needs (no settings per job, no format selection, no
  authentication).
- No data-profiling CLI: that is the `data-profiling-tool` EPIC.
- No continuous deployment; images are published, not deployed.
- No migration of old reports (DEC-16).

---

## What Changes

- `pyproject.toml` + `uv.lock` replace `requirements/`, `requirements.txt` and `setup.cfg`; Python
  3.13; current dependency majors (DEC-6, DEC-7).
- Root tool configs (`ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`, `.importlinter`,
  `.pre-commit-config.yaml`) and the standard Makefile targets (`install`, `lint`, `typecheck`,
  `check-architecture`, `check-spec`, `test`, `test-containers`, `check-all`) (DEC-9).
- The `fingerprinter` package restructured into `domain`, `services`, `adapters`, `entrypoints`
  (`api`, `ui`, `worker`) and a composition root (DEC-8).
- `rdf-fingerprinter` 3.5 through `fingerprint_report`; every format and the pitfall scan (DEC-1,
  DEC-2, DEC-3).
- **BREAKING**: report downloads by format name; job state with failures (DEC-5, DEC-11).
- **BREAKING**: custom report templates removed (DEC-4).
- The Flask UI on Flask 3 with per-format downloads (DEC-10).
- Tests split into `unit/`, `feature/`, `integration/`, `e2e/`; container tests against Fuseki,
  Redis and a Celery worker.
- `infra/` replaces `docker/`; `.env.example` replaces the committed `.env` files; GHCR replaces
  Docker Hub; CI runs `make check-all` and the container tests (DEC-12, DEC-13).
- `bash/` removed (DEC-14); `README.md` and the docs updated; `CHANGELOG.md` and `SECURITY.md`
  added.

## Capabilities

### New Capabilities
- `fingerprinting-jobs`: start a fingerprinting job for a SPARQL endpoint or an uploaded file, run
  the library with the pitfall scan, write every output, clean up the temporary dataset, and report
  the job's state and failures.
- `report-access`: list reports, download a report's outputs by format or as one zip, delete
  reports.
- `package-boundaries`: the layering of the `fingerprinter` package and the rule that only one
  adapter imports the library, checked by import-linter.

### Modified Capabilities

## Impact

- Code: all of `fingerprinter/`; `tests/`; the OpenAPI contract
  (`entrypoints/api/openapi/fingerprinter.yml`); the UI templates.
- Dependencies: every runtime and development dependency; `rdf-fingerprinter` 3.5.
- Systems: Fuseki, Redis, the Celery worker and Flower in `infra/`; GHCR.
- Users of the API: the report download changes (BREAKING).
- Unblocks: `data-profiling-tool` (DEC-4 points 4 and 5, DEC-6 of that EPIC).
