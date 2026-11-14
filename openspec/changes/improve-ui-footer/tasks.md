> Derives from: EPIC improve-ui-footer (`proposal.md`, DEC-1 to DEC-7); design F-1 to F-6.

One stage, one PR into `develop` through the stage loop, `make check-all`, `make test-containers`
and `make build-images` green. Scenario sign-off: `design.md`, Tests.

## 1. The footer (DEC-1 to DEC-7; F-1 to F-6)

- [x] 1.1 F-2: `infra/docker/Dockerfile` installs the project (non-editable) and the `base` stage
  no longer copies `fingerprinter/`. Test first in `tests/unit/test_infra_env.py`: the builder
  stage installs the project with `--no-editable`, and no later stage copies `fingerprinter`.
  Check: `make build-images`, then in the UI image `importlib.metadata.version` answers the version
  of `pyproject.toml`, and `templates/base.html`, `static/app.css` and the OpenAPI file are found
  under the installed package; the API image builds its app. Update the Dockerfile's description
  in `docs/modules/ROOT/pages/` where it says how the code gets into the image.
  Files: the Dockerfile, `tests/unit/test_infra_env.py`, docs.
- [ ] 1.2 F-1, F-3 to F-6: the `version` global in `ui/__init__.py`; the constants in
  `ui/labels.py`; `heart` and `meaningfy` in `templates/icons.html`; the footer in
  `templates/base.html`; the layout and the pulse in `static/app.css`. Tests first:
  `tests/feature/job_console.feature` and `tests/feature/test_job_console.py` (the first three
  scenarios); `tests/unit/ui/test_layout.py` ("The pulse stops under reduced motion"; the footer
  holds no `<script>` and no `style` attribute; the logo carries no `#212c4a`).
  Files: those named, nothing under `infra/`.
- [ ] 1.3 The stage PR: full gates, the review pass (L2 + L3), fixes.

## Test map

| Spec · scenario | Tier · file |
|---|---|
| job-console · Every page ends with the footer | feature · `tests/feature/test_job_console.py` (outline over the four pages) |
| job-console · The footer shows the installed version | feature · `tests/feature/test_job_console.py` |
| job-console · The heart is hidden from assistive technology | feature · `tests/feature/test_job_console.py` |
| job-console · The pulse stops under reduced motion | unit (`@unit` in the feature file) · `tests/unit/ui/test_layout.py` |
| job-console · The image knows its version | unit (`@unit`) · `tests/unit/test_infra_env.py` pins the Dockerfile; the built image is checked in task 1.1 and by CI's `images` job |
| report-viewer · Both themes pass (existing, now with the footer on every page, also at 360 px) | e2e · `tests/e2e/ui/test_accessibility.py` |

## Roadmap

- [x] 1.1 · [ ] 1.2 · [ ] 1.3

## Verification

`make check-spec`; the clarity gate (≥ 9/10) on this PLAN (`evidence/clarity-gate.md`);
`make check-all`, `make test-containers`, `make build-images`, `make check-docs` green; the
acceptance demo (the footer on both themes and at 360 px) in `evidence/acceptance.md`.

## Docs

Decided at accept (`evidence/docs-owed.md`).

## Close

Archive the change; `job-console` gains the requirement.
