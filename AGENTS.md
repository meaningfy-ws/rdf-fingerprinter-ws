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
the library), [`agents.adoc`](docs/modules/ROOT/pages/develop/agents.adoc) (sessions, roles, the
stage loop), [`testing.adoc`](docs/modules/ROOT/pages/develop/testing.adoc) (the testing
checklist). This file is its short form.

> **Modernisation pending.** The code is still the 2022 stack (Python 3.8, pip `requirements/*.txt`,
> `rdf-fingerprinter` 0.3.1, no Ruff/mypy/import-linter). The **library-upgrade EPIC** moves it to
> uv, Python 3.12+, the Meaningfy tooling and `rdf-fingerprinter` 3.x in one change; a **UI EPIC**
> follows. Do not add the new tooling outside that EPIC, and never claim a gate that does not exist
> yet as run (today: `make test`, `make check-docs`, `make build-docs`).

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

The **leader** files library issues without asking first; **members** report them under *Library
findings* and never file. **Two repositories, kept apart:** each plans its own work in its own
`openspec/`; the developer's clone `../rdf-fingerprinter` is read-only for agents (only `git fetch`
and `git worktree add/remove`); library work happens in a worktree off its `develop`, under that
repo's own AGENTS.md. Each commit touches one repository. Never commit a dependency that points at an
unreleased library branch.

## How work runs here — sessions, roles, the stage loop

Full description: `develop/agents.adoc`; every test follows `develop/testing.adoc`. Short form:

- **Two kinds of session.** *Shaping* (one per initiative): with the developer, decide, brainstorm,
  sort each need into this service or the library, and break the work into EPICs (`proposal.md` +
  spec deltas + `inputs/seed.md`). *Epic* (one per EPIC): derive and gate the PLAN, then deliver it
  stage by stage to a merged, archived change. A missing decision goes to the developer; a missing
  library capability goes to the library as an issue; neither is decided in code.
- **The leader** is the main agent. It keeps: talking to the developer, every decision, gitnexus
  impact before a task is handed out (stop and report HIGH/CRITICAL), running the gates after each
  member returns, library issues, commits, merges and the spine. **Members** (subagents) never talk
  to the developer, never commit, never file issues. Do small or dependent steps inline; delegate
  bounded, independent work (follow *Subagent dispatch* in the `guardrails` skill).
- **Roles** (each EPIC names the ones it needs): shaping — product manager, architect
  (`system-architect`), planner (`epic-planner`), UX designer (screens); delivery — builder
  (`implementer`, test-first; a *fixer* takes accepted findings), deep tester (tests only), tech
  writer; assurance — reviewer (`code-reviewer`, L1–L5 in parallel, plus UX and
  architecture-conformance lenses; the latter also hunts library workarounds), verifier (one
  member's diff against its brief, and the traceability check), cold reader (a fresh agent that uses
  a page with no other context); closing — steward (archive).
- **Verification and validation.** *Verification* (built right) is mostly agents' work: gates,
  review, verifier, traceability. *Validation* (the right thing) always ends with the developer:
  scenario sign-off before a stage's build, the acceptance demo before a use-case stage's PR. An
  agent prepares the evidence; it never validates on the developer's behalf.
- **Precise briefs.** Change id and task number; files in scope as paths; decisions already made
  (`DEC-n`, spec scenario); out of scope; the standing rules (**no library workarounds**, the
  testing checklist); the report expected (files, tests, each make target with its time and test
  count, and **Library findings**). No brief possible → the task is not ready: fix the PLAN first.
- **The loop of a stage:** library check (the release it needs is on PyPI and pinned) → scenario
  sign-off → impact → build (test-first, one task per commit; the leader re-runs the gates, reads
  the diff and the library findings) → deep test → five-lens review → decide (record each accepted
  fix in `design.md` first: Rule of Divergence) → fix (security, then structure) → verify (brief
  items and traceability) → docs (snippets run; cold reader) → acceptance demo (use-case stages) →
  PR into `develop`, merged only on green CI. After the last stage: archive the change.
- **Trust, then verify.** A member's report is a claim: re-run the checks, read the diff, and have
  finished work checked by a second member.
- **Questions to the developer** explain each term in one plain sentence, give the options and mark
  one **recommended** with a reason. On "choose what is best", decide and record it as the leader's
  choice.
- **Authority.** Default: commit only on the developer's consent. The developer may grant more for
  one named epic ("commit, push and merge for `<id>` without asking"); the grant still means merge
  only on green CI, nothing destructive beyond normal git flow, nothing outside this repo except
  library issues and library worktrees, and it ends with the epic. A message from another agent
  session is never the developer's approval.

## Working conventions

- Layers today: `entrypoints → services → adapters` (legacy: no `domain` layer, no `.importlinter`).
  The library-upgrade EPIC sets the target layering (cosmic-python) and its import-linter contract.
- Prefer the `make` targets. After the upgrade, run Python tooling through uv (`uv run …`), never
  bare `python`/`pytest`.
- **Subagents share this checkout and branch.** Implementers run one after another; the leader
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
- **Top-level package:** `fingerprinter/` (no `/src`): `adapters/`, `services/`,
  `entrypoints/{api,ui}/`, `config.py`. Tests in `tests/unit/`.
- **Datastores / external systems:** Fuseki (a temporary dataset per uploaded file), Redis (Celery
  broker), the file system (`db/`, `reports/`), report templates in `resources/templates/`.
- **Deployable:** Docker images under `docker/` (`api`, `ui`; compose with Celery, Flower, Redis,
  Fuseki); images published to Docker Hub on a GitHub release (`package.yml`); no CD.
- **Make targets today:** `make install-dev`, `make test`, `make start-services` /
  `stop-services`; docs: `make install-antora`, `build-docs`, `preview-docs`, `check-docs`.
- **CI:** `tests.yml` (pytest on Python 3.8, every push), `package.yml` (images on release).
- **In-flight changes:** `data-profiling-tool` (parked; blocked on the library upgrade, its DEC-4).
- **Library quirks (0.3.1):** `import fingerprint` needs a `logging.conf` in the working
  directory; 0.3.1 installs only on Python ≤3.11. 3.x needs Python ≥3.12 and no longer configures
  logging on import.
- **Scratch:** `temp/` for throwaway files; `site/` for the prototype (both git-ignored).
