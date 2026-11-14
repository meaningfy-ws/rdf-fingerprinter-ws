# Design: improve-ui-footer

> Derives from: EPIC improve-ui-footer (`proposal.md`, DEC-1 to DEC-7). Inputs: `inputs/seed.md`,
> `inputs/meaningfy-logo.svg`. Builds on `modernise-user-interface` (archived): its U-1 (assets and
> theme) and U-2 (labels) still hold.

## Context

The UI is a Flask 3 app (`fingerprinter/entrypoints/ui/`). `base.html` ends with
`<footer class="site-footer">Powered by …</footer>`; every page, the error page included, extends
`base.html`. `create_app` registers Jinja globals (`labels`, the flash names). Icons are inline SVG
macros in `templates/icons.html`. `app.css` already holds `--danger`, `--muted`,
`.visually-hidden`, and a global `@media (prefers-reduced-motion: reduce)` rule that sets
`animation: none !important` on `*`.

The package is installed where the tests run (`uv sync`), so
`importlib.metadata.version("rdf-fingerprinter-ws")` answers `0.1.0`. The images are different:
the Dockerfile runs `uv sync --no-install-project` and copies `fingerprinter/` beside the virtual
environment, so the package has no metadata there and the call would raise at start-up.

## Decisions (how)

- **F-1 The version** (DEC-6). `create_app` adds the Jinja global `version`, read once with
  `importlib.metadata.version("rdf-fingerprinter-ws")`. No fallback: a missing package fails at
  start-up, where F-2's check catches it. No setting, no argument to `create_app`.
- **F-2 The images install the package** (DEC-6; the developer, 2026-11-14, answering "how should
  the image know its version": install the package). The builder stage keeps the dependency layer
  (`uv sync --frozen --no-default-groups --no-install-project` on the two lock files), then copies
  `fingerprinter/` and runs `uv sync --frozen --no-default-groups --no-editable`, which installs
  the project into `/opt/venv`. The `base` stage no longer copies `fingerprinter/`: the one copy of
  the code is the installed one, owned by root. `uv_build` packs every file under the module
  (`[tool.uv.build-backend]` in `pyproject.toml`); the check of F-6 proves the templates, the
  stylesheet and the OpenAPI file arrived. This amends the EPIC's Impact line ("no infrastructure
  change"), logged in `proposal.md`.
- **F-3 The copy** (DEC-2, DEC-5; U-2). `ui/labels.py` gains the footer's words and addresses as
  constants: the three URLs (`https://meaningfy.lu`,
  `https://github.com/meaningfy-ws/rdf-fingerprinter-ws`,
  `https://github.com/meaningfy-ws/rdf-fingerprinter-ws/blob/main/LICENSE`), "Made with", "love",
  "by", "Meaningfy", "GitHub", "Apache-2.0". The template holds none of them.
- **F-4 The markup** (DEC-1, DEC-4, DEC-5). In `base.html`, inside `<footer class="site-footer">`:
  - a credit `<p>`: "Made with", the heart (`<span class="heart" aria-hidden="true">` holding
    `icons.heart()`), a `.visually-hidden` "love", "by", and one link to the website whose content
    is `icons.meaningfy()` plus a `.visually-hidden` "Meaningfy";
  - a second `<p>`: the repository link "GitHub", the licence link "Apache-2.0" and
    `v{{ version }}`, separated by "·" marked `aria-hidden`.
  All three links carry `rel="noopener"`; none opens a new tab. The footer's text content,
  whitespace collapsed, starts "Made with love by Meaningfy".
- **F-5 The icons** (DEC-3, DEC-4). `icons.html` gains `heart(size)`, through the existing `_icon`
  macro with a filled path, and `meaningfy()`, its own `<svg>` (`viewBox="0 0 1800 299.999988"`,
  `fill="currentColor"`, `aria-hidden`, `focusable="false"`, class `logo-meaningfy`) holding the
  two paths of `inputs/meaningfy-logo.svg` unchanged, without their `fill="#212c4a"`.
- **F-6 The style** (DEC-1, DEC-3, DEC-4). In `app.css`: `.site-footer` becomes a wrapping flex row
  (`justify-content: space-between`, the width of `main`), centred in a column under `40rem`;
  `.logo-meaningfy` is `1.25em` high, width auto, aligned to the text; the logo link takes
  `color: inherit`; `.heart` is `color: var(--danger)` with `animation: pulse 1.6s ease-in-out
  infinite` and `@keyframes pulse` scaling to 1.2. The existing reduced-motion rule already stops
  it; the animation is declared without `!important` so that rule wins.

## Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Write `0.1.0` in a template or in `labels.py` | F-1 | It goes stale at the first release (DEC-6) |
| Catch `PackageNotFoundError` and show "dev" | Let it fail; fix the install (F-2) | A released image would hide its version |
| Read `pyproject.toml` at run time | `importlib.metadata` | The file is not in the image |
| Use the ❤ emoji or an `<img>` logo | Inline SVG with `currentColor` | Emoji vary by platform; an image cannot follow the theme |
| Give the logo the navy `#212c4a` | `currentColor` | Unreadable on the dark theme (DEC-3) |
| Add a script, or `!important` on the pulse | CSS only, plain declaration | No-go; and the reduced-motion rule must win |
| `target="_blank"` on the links | Plain links with `rel="noopener"` | Nobody asked for new tabs |
| Keep a second copy of `fingerprinter/` in `/app` | One installed copy (F-2) | Two copies drift and one shadows the other |

## Error matrix

| Case | Result |
|---|---|
| The package is not installed (an image built the old way) | The UI fails at start-up with `PackageNotFoundError`; caught by task 1.1's check, never shipped |
| The API is unreachable or answers an error | The error page still ends with the footer (it extends `base.html`) |
| A screen under `40rem` | Two centred lines, no horizontal scroll (the e2e 360 px check) |
| `prefers-reduced-motion: reduce` | The heart is still |
| An editable install after a version bump without `uv sync` | The old version is shown until the next sync; accepted, development only |

## Tests

The requirement is in `specs/job-console/spec.md`; the test map is in `tasks.md`. The feature tier
gains `tests/feature/job_console.feature` (one scenario per spec scenario, same name) bound in
`tests/feature/test_job_console.py` over the UI's test client and `tests/unit/ui/fake_api.py`.
Scenario sign-off: the developer approved "What it must prove" in `inputs/seed.md` (2026-11-14),
which these scenarios restate; "The image knows its version" follows from the developer's answer
recorded in F-2.

## Risks / Trade-offs

RISK-1 to RISK-4 of the EPIC stand, accepted. Added by this PLAN:

- **RISK-5** `uv_build` leaves a non-Python file out of the installed package. Low likelihood,
  high impact (a UI without templates). Mitigated: task 1.1's check reads them from the built
  image; `make test-containers` and CI's `images` job stay green.
- **RISK-6** The wordmark is hard to read at `1.25em`. Medium likelihood, low impact. The
  acceptance demo shows it on both themes; the answer is a larger height (the EPIC's rabbit-hole),
  the developer decides.

## Delivery decisions

- **D-1** Blast radius (2026-11-14): `create_app` keeps its signature; its callers are
  `bootstrap.ui_app` and the tests' `make_app`. The code index was 33 commits behind and answered
  UNKNOWN; refreshed, it answers LOW (3 direct callers, one process, `ui_app`).
- **D-2** Tasks 1.1 and 1.2 touch disjoint files and run in parallel. Task 1.1's gate is narrower
  than `make check-all` (its own unit file and the image build), so that neither builder judges
  the other's half-done work; the lead runs the full gates on both together.

## Review decisions (stage 1, PR #43, one pass L2 + L3, 2026-11-14)

Accepted:

- **R-1** (W1) The data folders do not depend on where the code is installed. `Settings.from_env`
  defaults `file_db` and `reports_db` beside the package, which F-2 moved into `site-packages`; an
  image started without the two variables would write there and fail. The `base` stage sets
  `RDF_FINGERPRINTER_FILE_DB=/app/db` and `RDF_FINGERPRINTER_REPORTS_DB=/app/reports`;
  `tests/unit/test_infra_env.py` pins it. `config.py` is not changed.
- **R-2** (W2) "The image knows its version" is checked by a command, not by hand:
  `make build-images` ends by asking the built UI image for its version (equal to
  `pyproject.toml`'s) and for `templates/base.html`, `static/app.css` and the OpenAPI file in the
  installed package. CI's `images` job runs that target, so the Test map's row becomes true.
- **R-3** (W3) The version test has its own oracle: with the UI's `version` function replaced by
  one answering a sentinel, the footer shows the sentinel. A version written in a template fails.
- **R-4** (S3, S4, S5) Tests that could pass for the wrong reason are tightened: the builder's
  `uv sync` line with `--no-editable` must lack `--no-install-project`; a `COPY` with flags or of
  `.` in a later stage is caught; the reduced-motion rule's selector must reach the heart; the
  "job that does not exist" row asserts `404`.

Corrected without a decision: the PR body's test count (S1: 651 before, 10 added). S2: CI is green.

To the developer: S6, the heart's red is about 2.9:1 on the dark theme (asked together with the
footer's layout, after the demo).

Rejected: none.
