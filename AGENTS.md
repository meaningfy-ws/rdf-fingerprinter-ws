<!-- meaningfy-template-version: 3.0.0 -->
<!-- CANONICAL, CLI-agnostic agent instruction file (opencode reads AGENTS.md natively; Claude Code
     reads it through the @AGENTS.md import in CLAUDE.md). Edit THIS file. CLAUDE.md is a thin
     pointer that adds only Claude-specific guidance — never a symlink, never a copy. This file
     ROUTES to skills and to the global standard; it never restates that standard. -->

# Project: RDF Fingerprinter WS

Meaningfy project. Build clean, layered, well-tested code; minimise WTFs-per-minute. The
company-wide standard (Clean Code, Clean Architecture, testing, tooling) lives in your **global
agent instructions** (`~/.claude/CLAUDE.md` on Claude Code, `~/.config/opencode/AGENTS.md` on
opencode) — this file does **not** repeat it; it ROUTES to it and to the installed skills, and
records only what is specific to **this** repo.

The full method, for people and agents, is the **developer runbook**
([`docs/modules/ROOT/pages/develop/`](docs/modules/ROOT/pages/develop/index.adoc)):
[`index.adoc`](docs/modules/ROOT/pages/develop/index.adoc) (method, structure, conventions),
[`rdf-fingerprinter.adoc`](docs/modules/ROOT/pages/develop/rdf-fingerprinter.adoc) (building on
the library), [`agents.adoc`](docs/modules/ROOT/pages/develop/agents.adoc) (what is specific
here when agents deliver; the method is skillery's `epic-delivery`), [`testing.adoc`](docs/modules/ROOT/pages/develop/testing.adoc) (the testing
checklist). This file is its short form.

> **Modernised (2026-11-08).** The library-upgrade EPIC (uv, Python 3.13, `rdf-fingerprinter` 3.6,
> Connexion 3 / Flask 3, the cosmic-python layering, every output format, `infra/`, the container
> tests) and the UI EPIC (the job console, report viewer, class diagrams and graph picker) are
> archived; their requirements are in `openspec/specs/`. The gates: `make check-all`,
> `make test-containers`, `make build-images`, `make check-docs`, `make build-docs`. Never claim
> one as run unless it ran.

## Skill routing (use the skill for the task)

- Structuring Python code (domain/adapters/services/entrypoints, SOLID, CI) → **cosmic-python**
- Keeping code minimal — YAGNI, avoid over-engineering, simplest working approach → **ponytail**
  (`/ponytail` to set intensity; `/ponytail-review` for a delete-list on the diff)
- System / solution design (C4, ADRs, contracts) → **architecture**
- Bringing the repo up to standard (part of the library-upgrade EPIC) → **project-setup**
- Building on the `rdf-fingerprinter` library → `develop/rdf-fingerprinter.adoc`
- Any new feature or non-trivial change → start by exploring options (**superpowers:brainstorming**)
- Any feature or bugfix implementation → **superpowers:test-driven-development** (tests first)
- Debugging → **superpowers:systematic-debugging**
- Shaping an EPIC + deriving its PLAN → **epic-planning** + the opsx workflow commands
  (`/opsx:*` on Claude Code, `opsx-*` on opencode)
- Spec readiness (the PLAN clarity gate, ≥9/10) → **clarity-gate**
- BDD features → **bdd-gherkin**
- Screens and flows (the UI) → **design** + **frontend-design**
- Commits / branches / PRs → **meaningfy-git-workflow** (mechanics via **commit-commands**)
- Pre-PR review → **meaningfy-code-review** (+ external **code-review**)
- Deploy / release / versioned image → **ci-cd-delivery**
- Docs → **technical-writing**

If a request conflicts with these, flag it before proceeding.

## The spine — where work is shaped and remembered

This repo carries the Meaningfy **spine** under `openspec/` (OpenSpec, schema `meaningfy`):

- **EPIC ≡ `openspec/changes/<id>/proposal.md`** (the Shape-Up work shape: appetite, why, solution,
  key decisions, rabbit-holes, no-gos).
- **PLAN ≡ `openspec/changes/<id>/design.md` + `tasks.md`** (the clarity gate scores the pair ≥9/10).
- **Normative requirements ≡ `openspec/changes/<id>/specs/<cap>/spec.md`** (RFC-2119 SHALL +
  Given/When/Then; no EARS). They merge into **`openspec/specs/`** — the durable truth — on archive.
- **Seed inputs** (briefs, notes) live in `openspec/changes/<id>/inputs/` — preserved, never groomed.
  **Evidence** (spikes, acceptance demos) lives in `openspec/changes/<id>/evidence/`.
- **Orientation** is `openspec/config.yaml`'s `context:` field (the native index) — **not** a
  hand-curated MEMORY.md. The truth is `openspec/specs/`.

Drive it with the opsx workflow commands (`/opsx:*` on Claude Code, `opsx-*` on opencode): `propose`,
`explore`, `apply`, `sync`, `archive` — core profile.

**External method skills land in the spine (binding).** `superpowers` provides *disciplines*, not a
parallel spec system — its artifacts MUST land in `openspec/changes/<id>/`, never a `docs/superpowers/`
tree. A **brainstorming** design feeds the **EPIC** (`proposal.md`); **writing-plans is SUPERSEDED** by
the **PLAN** (`design.md`+`tasks.md`); execution uses superpowers TDD, tracked via the opsx `apply`
command.

**Golden thread (cite your parent).** Each artifact cites the one above it: the PLAN (`tasks.md`)
cites its EPIC id on the first line; specs cite their capability; commits reference the change. This
is how any commit traces up to the requirement that justifies it.

## rdf-fingerprinter — the library, held to a strict standard

This service wraps the **`rdf-fingerprinter`** library (`meaningfy-ws/rdf-fingerprinter`, PyPI
`rdf-fingerprinter`, import name `fingerprint`), in its own repository. The library does the
fingerprinting (the queries, the statistics, the reports); this service adds the API, the UI, the
asynchronous jobs, file upload into Fuseki and report packaging. Full map:
`develop/rdf-fingerprinter.adoc`.

**No workarounds. Ever.** When the library has a bug, a gap in its docs, an awkward API or lacks a
capability this service needs, the service does **not** compensate. Never: patch, monkeypatch or
subclass library internals; import a private submodule; copy library code; write SPARQL, a report
renderer or a statistic that is the library's job; post-process its output to correct it; weaken a
requirement, test or check to fit; leave a shim, `TODO` or skipped test standing in for the fix.
Instead:

1. **Stop** the task (other tasks may go on). Reproduce the problem with the library alone and
   confirm it is the library's, not a misuse.
2. **Search** open issues (`gh issue list -R meaningfy-ws/rdf-fingerprinter --search "…"`);
   comment on a match instead of duplicating.
3. **File a GitHub issue** in `meaningfy-ws/rdf-fingerprinter` in the shape of
   `develop/rdf-fingerprinter.adoc#issue`, written **generically** (this service named only under
   Context).
4. **Record** it: `tasks.md` marks the task `blocked by meaningfy-ws/rdf-fingerprinter#<n>`;
   `design.md` lists it under library dependencies.
5. **Tell the developer**: the link, what is blocked, what goes on. The developer schedules the fix.
6. **Resume** only after the fix is released to PyPI and this repo's pin is raised in its PR.

The **lead** files library issues without asking first; **members** report them under *Library
findings* and never file. **Two repositories, kept apart:** each plans its own work in its own
`openspec/`; the developer's clone `../rdf-fingerprinter` is read-only for agents (only `git fetch`
and `git worktree add/remove`); library work happens in a worktree off its `develop`, under that
repo's own AGENTS.md. Each commit touches one repository. Never commit a dependency that points at an
unreleased library branch.

## How work runs here — sessions, the team, the stage loop (developer, 2026-11-08)

The method (shaping and epic sessions, the team and its briefs, the six-step stage loop scaled by
appetite, the lead's authority, the question format, verification vs validation, the rule for our
own and external libraries) is skillery's **epic-delivery** skill (bundle `meaningfy-building`
>= 3.9.0); shaping is **epic-planning**; subagent dispatch and session hygiene are **guardrails**
(`meaningfy-core`). Work that way every time. The page for people is `develop/agents.adoc`; every
test follows `develop/testing.adoc`. What this repo adds:

- **Every brief carries the standing rules:** no library workarounds; the testing checklist. The
  report names each make target run with its time and test count, and a **Library findings**
  section (members report; only the lead files issues).
- **Gates.** Before a stage, every library release it needs is on PyPI and pinned. Before a task is
  handed out, the lead runs gitnexus impact (stop and report HIGH/CRITICAL); after it, the lead
  re-runs the `make` gates listed in `develop/agents.adoc`.
- **Merge.** One PR per stage into `develop`, merged only on green CI.

## Working conventions

- Layers (cosmic-python, enforced by import-linter, `make check-architecture`): `bootstrap` over
  `entrypoints` and `adapters`, over `services`, over `domain`; imports go downward only.
- Prefer the `make` targets. Run Python tooling through uv (`uv run …`), never bare `python`/`pytest`.
- **Subagents share this checkout and branch.** Implementers run one after another; the lead
  commits after each task. Parallel writers only on disjoint files, and they never stage or commit.
  Read-only agents may run in parallel freely. Use a worktree (`isolation: "worktree"`) only for
  overlapping parallel work or when another session holds this checkout.
- **Temporary files** go in `temp/` (git-ignored), not `/tmp` or the session scratchpad. `site/`
  (git-ignored) holds the data-profiling prototype the `data-profiling-tool` EPIC refers to.
- **Branches:** off `develop`; PRs target `develop`; `main` receives releases only. Never commit to
  `main` or `develop` directly.
- **Commits and PRs carry no AI attribution** (no `Co-Authored-By`, no "Generated with" line).
  Enforced for Claude Code by `.claude/settings.json` (`attribution` empty); other agents follow
  this rule by hand.
- **Commit messages give the why and the what.** Subject: Conventional Commit, imperative, no
  trailing period (`feat(api): accept Turtle uploads`). Body, after one blank line, wrapped at ~72
  columns: **Why** (the problem or constraint), **What** (one bullet per concern, naming the main
  files), **Trace** (`Refs: <change-id> DEC-n`; a `BREAKING CHANGE:` line when it applies). A
  one-line body is fine only for trivial changes.

## `.claude/` is a regenerable index — the truth is `openspec/specs/`

`.claude/memory/MEMORY.md` is a cheap orientation note (≤200 lines; stable patterns only). It is an
**index, not authority** — if it disagrees with `openspec/specs/`, `specs/` wins. Do not introduce
parallel epic files under `.claude/`.

## Project specifics

- **Archetype:** product — a Flask API (Connexion, OpenAPI in `entrypoints/api/openapi/`) and a
  Flask UI (Jinja templates) with Celery workers, wrapping `rdf-fingerprinter`.
- **Top-level package:** `fingerprinter/` (no `/src`): `domain/`, `services/`, `adapters/`,
  `entrypoints/{api,ui,worker}/`, `config.py`, `bootstrap.py`. Tests in `tests/{unit,feature,integration,e2e}/`.
- **Datastores / external systems:** Fuseki (a temporary dataset per uploaded file), Redis (Celery
  broker), a PlantUML server (class diagrams), the file system (`db/`, `reports/`).
- **Stack hardening:** `infra/compose.yaml` has four networks (`edge` has a route out; `app`, `work`,
  `monitor` are internal); the API and worker reach user URLs only through the Squid egress proxy
  (`infra/proxy/squid.conf`, `NO_PROXY=fuseki,plantuml`); nginx (`infra/edge/`) publishes the UI and
  API on loopback; Redis, Fuseki and PlantUML are published only by `infra/compose.dev.yaml`
  (`make up-dev`, `make up-deps`); each container holds only its secrets (no `env_file`);
  `make init-env` writes `infra/.env`; `tests/unit/test_infra_env.py` pins all of it.
- **Deployable:** `infra/` holds `compose.yaml`, `.env.example` and one multistage non-root `docker/Dockerfile`
  (targets `api`, `ui`, `worker`; Python 3.13, uv); images are published to
  `ghcr.io/meaningfy-ws/rdf-fingerprinter-ws-{api,ui,worker}` on a GitHub release (`release.yml`); no CD.
- **Make targets:** `make install`, `make check-all` (= `check-quality` + `test`), `lint`,
  `typecheck`, `check-architecture`, `check-spec`, `test`, `test-containers`; the stack: `make init-env`,
  `up`, `up-dev`, `up-deps`, `down` (needs no `.env`), `rebuild`, `build-images`, `logs`, `run-api`, `run-ui`,
  `run-worker` (settings in `infra/.env`, written by `make init-env` from `infra/.env.example`); docs: `make install-antora`, `build-docs`, `preview-docs`, `check-docs`.
- **CI:** `ci.yml` (`check-all`, the `containers` job and the `images` job on Python 3.13, PRs into and pushes to
  `develop`), `docs.yml`, `release.yml` (images to GHCR on a release); every action is pinned to a
  commit SHA with its tag in a comment.
- **In-flight changes:** `data-profiling-tool` (parked; DEC-4 points 4-5 and DEC-6 resolved by the
  upgrade; points 1-3 and 6 to check against the library when it resumes). Archived:
  `upgrade-fingerprinter-library`, `modernise-user-interface`. Open library issues the service
  waits on: `meaningfy-ws/rdf-fingerprinter#69`, `#75`, `#76`, `#77`.
- **Library quirks (3.6.0):** typed (`py.typed`); `list_named_graphs` lists an endpoint's named
  graphs (for the UI's graph picker); it configures no logging on import; `resolve_settings` lives in
  `fingerprint.service_layer.settings`.
- **Scratch:** `temp/` for throwaway files; `site/` for the prototype (both git-ignored).
