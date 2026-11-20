---
kind: seed notes (secondary; superseded by proposal.md, never groomed)
---

# Handover — data profiling tool

The seed for this change. No `proposal.md` exists yet: shape the EPIC with `/opsx:propose
data-profiling-tool` (skill `epic-planning`), using this note as input.

**This repository is public.** Keep client names, namespaces, IRIs, counts and outputs out of
anything committed here. Client-specific findings live in the consuming project (below).

## Goal

Turn the throwaway scripts in `site/` (git-ignored) into a small, generic, tested profiling tool in
this repository. It profiles an RDF dataset fast and emits:

- a JSON fingerprint;
- a readable report with prefixes;
- PlantUML class diagrams;
- descriptive SHACL shapes.

The first consumer is the `brainframe-mcp` project (local: `~/work/repos/brainframe-mcp`). There the
change `openspec/changes/schema-from-data-profile/` needs it (its DEC-5). Its
`inputs/fingerprint-run-notes.md` holds the client-specific findings and the measured numbers.

## What exists (the prototype in `site/`, working, untested)

| file | does |
|---|---|
| `fuseki.sh` | Docker `stain/jena-fuseki`, in memory, `ADMIN_PASSWORD=local`. Data goes to the default graph, the ontology to the named graph `<urn:ontology>`. Paths are env-overridable (`DATA_DIR`, `DATA`, `ONTO`); defaults point at the consumer's `data/`. |
| `namespaces.sh` | Namespace census by role: predicates, classes, subjects, IRI objects. |
| `profile.py` | Standard library only. Four whole-graph SPARQL queries: instance counts per class, and per class-property pair the subject count, min/max cardinality, triples and object types. It adds labels and direct superclasses from `<urn:ontology>` and writes `out/profile.json`. |
| `render.py` | Standard library only. From `profile.json` it writes `report.md`, `schema.puml` (full), `schema-hierarchy.puml` (inheritance only), `shapes.ttl` (descriptive SHACL) and `prefixes.json` (in the library's HTML format). |
| `html.sh` | The library's HTML report, using the library template but our `prefixes.json`. Runs from the repo root because of `logging.conf`. |

Order: `./fuseki.sh && python3 profile.py && python3 render.py && ./html.sh`, then
`(cd out && plantuml -tsvg *.puml)`. The rendered SHACL was checked to parse with rdflib (51 node
shapes and 620 property shapes on the first dataset). Nothing else is tested.

## What the prototype proved

- **Speed**: the same statistics in a few whole-graph queries take about 3 s. The library takes over
  2 min, because it runs one heavy query per class, twice when it renders both HTML and JSON
  (`fingerprinter/services/report_handling.py`, `fingerprint_sparql_endpoint`).
- **Ontology loading**: useful only in a separate named graph, for labels and the hierarchy. Mixed
  into the profiled graph, its declarations would be profiled as data.
- **Prefixes**: readability depends on separating schema namespaces from data namespaces. Data IRIs
  can follow a `{base}/{Collection}/{id}` pattern that gives one prefix per collection.
- **Diagrams**: the hierarchy-only view is readable. The full view is a hairball, because a handful
  of properties occur on nearly every class.

## Must change before it becomes product code

- **Client-specific constants are hard-coded** in `profile.py`: the schema prefix map, `DATA_BASE`,
  and the ontology namespace check in `render.py` (`SCHEMA_NS`). Make them inputs (a prefixes file,
  a data-base IRI, or both) so the tool is generic.
- **Namespace classification** (schema or data) is a prefix-list heuristic. Decide whether it is a
  rule (IRIs in class or predicate position are schema) or configuration.
- **Instance IRIs used as predicates** are counted and left out of the diagram and the shapes.
  Decide how the tool treats them; the consumer has the same question open (its DEC-6).
- **Full diagram**: factor the common properties into a shared base class or a note.
- **SHACL semantics** are descriptive and observed, not intended:
  - `sh:minCount` only when every instance has the property;
  - `sh:maxCount 1` only when no instance has more than one value;
  - `sh:datatype`, `sh:class` or `sh:or` from the observed types;
  - `sh:nodeKind sh:BlankNodeOrIRI` for untyped objects.

  Keep this, and say it in the output.

## Decisions to make while shaping

1. **Form**: a standalone CLI module (for example `fingerprinter/profiling/` with a `__main__`, or a
   separate top-level package), or a new API/Celery task in the existing service. Recommended: a CLI
   first. The consumer runs it manually, and the service needs Redis and Celery to run anything.
2. **Triplestore**: keep Fuseki via Docker (already a dependency of `make start-services`), or load
   the files with rdflib in memory. Fuseki was fast; rdflib is untested on large files.
3. **Relation to the `rdf-fingerprinter` library**: replace its use for this purpose, or keep its
   HTML report as an optional output. Its defects (below) argue for replacing it.
4. **Python version**: the service's Docker images use 3.8, and the library does not install on
   3.12 or later. The prototype is standard library only and runs on 3.14.

## Gotchas

- The library fails on import (`import fingerprint`) unless `logging.conf` is in the working
  directory.
- `rdf-fingerprinter` 0.3.1 needs Python 3.11 or lower: `uv tool install --python 3.11
  rdf-fingerprinter==0.3.1`.
- `resources/templates/json/` is a stub with no `main.json`, so the library has no JSON report.
- The library HTML compacts property and type IRIs through `prefixes.json` (keys end in `:`), but not
  the class headings.
- `stain/jena-fuseki` rejects uploads with HTTP 401 unless `ADMIN_PASSWORD` is set.
- Fuseki's `--file` loads a single file; to load several, start it with `--mem --update` and POST
  each file.

## Repository state at handover (nothing committed)

- **This repository**: the minimal Meaningfy setup (`openspec/` with the `meaningfy` schema pinned
  at 1.4.1, `AGENTS.md`, the `CLAUDE.md` pointer, `.claude/` with the `/opsx:*` commands and
  `memory/MEMORY.md`), plus this note. Not committed; branch off `main` before committing. The
  legacy tooling (requirements files, `setup.cfg`, no Ruff, mypy or import-linter) was deliberately
  left alone; modernising it is a separate change.
- **The consumer** (`brainframe-mcp`), uncommitted:
  - DEC-5 and DEC-6 added to `schema-from-data-profile/proposal.md`;
  - the new `inputs/fingerprint-run-notes.md`;
  - an untracked `fingerprint-report/` from the first run, safe to delete;
  - the owner's own `.gitignore` edit, left untouched.
- **Running**: the Docker container `rdf-fp-fuseki` on port 3030. Stop it with
  `docker rm -f rdf-fp-fuseki`.
- **Installed**: the `fingerprint` CLI (via `uv tool`, Python 3.11) and `plantuml`.
