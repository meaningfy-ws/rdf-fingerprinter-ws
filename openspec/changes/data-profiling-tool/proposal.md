# EPIC: Data profiling CLI on the upgraded rdf-fingerprinter library

> Golden thread: first EPIC in this repository; no parent spec yet. Seeds: `inputs/handover.md`
> (the prototype in `site/` and what it proved), `inputs/elicitation.md` (the answers given while
> shaping). The consumer's own findings stay in the consuming project, named in the handover.
>
> **Status: parked.** Blocked on an upgrade of the `rdf-fingerprinter` library (DEC-4), which the
> owner is doing. Resume by checking the upgraded library against the list in DEC-4, deciding DEC-5
> to DEC-7, then deriving the PLAN (`design.md` + `tasks.md`) and the spec delta.

## Appetite

**MEDIUM**. One new capability, a profiling CLI, with its tests and docs. The profiling itself comes
from the upgraded library; this repository adds the input handling, prefixes and the renderers it
does not provide. The existing API and UI are touched only if the library upgrade breaks them.

## Why

Profiling an RDF dataset with the library today takes minutes, gives no usable JSON, and produces a
report that is unreadable without prefixes. A throwaway prototype showed the same statistics in
seconds, with readable prefixes, class diagrams and descriptive SHACL. A consuming project needs
that output now, from a tested, generic tool rather than git-ignored scripts.

## Solution outline

A command-line tool in the `fingerprinter` package profiles one dataset and writes a folder of
outputs:

- the JSON fingerprint (from the library);
- a readable report with prefixes;
- PlantUML class diagrams, full and hierarchy only;
- descriptive SHACL shapes, which state that they describe the data as observed, not as intended;
- the prefix map the library's HTML report uses.

The tool takes a SPARQL endpoint, or data and ontology files that it loads into a temporary
Fuseki dataset: data in the default graph, the ontology in a named graph. Prefixes come from the
data itself, with an optional file to override them, so nothing about a particular dataset is
hard-coded.

## Key decisions

- **DEC-1**: A CLI entrypoint in the `fingerprinter` package (`entrypoints/cli`, on `click`), with
  the logic in services and adapters so the API could call it later. Reason: the consumer runs it
  by hand, and the service needs Redis and Celery to run anything. Rejected: a new API/Celery task;
  committing the scripts as a loose `tools/` folder.
- **DEC-2**: Namespace roles are inferred, and an optional file overrides them. A namespace is
  schema when it holds classes or predicates, and data when it holds only subjects or objects.
  Common vocabularies get their usual prefixes; the override file sets prefixes, roles and data-IRI
  patterns such as `{base}/{Collection}/{id}`, which give one prefix per collection. Rejected: a
  required configuration file (a first run needs hand-written config); inference only (unreadable
  generated prefixes).
- **DEC-3**: Input is either `--endpoint URL` or `--data FILE [--ontology FILE]`. Files are loaded
  into a temporary Fuseki dataset by reusing `upload_file_to_dataset`, extended to load the
  ontology into a named graph. The profiled graph is the default graph only. Rejected: rdflib in
  memory (slow and untested on large files, and a second query engine to test); endpoint only.
- **DEC-4**: The profiling is done by the `rdf-fingerprinter` library, upgraded by the owner, not
  by this repository's own queries. This EPIC needs the upgraded library to:
  1. profile in a few whole-graph queries, not one heavy query per class (the prototype takes about
     3 s, the library 0.3.1 over 2 min);
  2. emit a JSON fingerprint with, per class, the instance count, and per class-property pair the
     subject count, min and max cardinality, triple count, and object types with distinct counts
     (class, datatype, or untyped IRI or blank node);
  3. profile the default graph only, and take labels and direct superclasses from a named
     ontology graph;
  4. import without a `logging.conf` in the working directory;
  5. install on current Python (3.12 and later);
  6. compact class headings as well as properties and types through the prefix map in its HTML report.

  *Points 4 and 5 resolved (2026-11-08, `upgrade-fingerprinter-library` archived):* rdf-fingerprinter
  3.6.0 configures no logging on import and installs on Python 3.13, which this service now uses.
  Points 1–3 and 6 are still to be checked against the library when this EPIC resumes.

  Rejected: replacing the library with the prototype's queries; keeping 0.3.1.
- **DEC-5 (open)**: Where each output comes from. The library could also produce the prefix
  inference, the SHACL and the PlantUML, or this repository renders them from the JSON. Decide once
  the upgraded library's scope is known.
- **DEC-6 (resolved 2026-11-08)**: The Python version. The service's images now run Python 3.13 with
  uv (`upgrade-fingerprinter-library`, `infra/docker/Dockerfile`), so the CLI can run in them.
- **DEC-7 (open)**: Instance IRIs used as predicates. The prototype counts them per class and
  leaves them out of the diagram and the shapes. Keep that, summarise them per collection, or
  describe them. The first consumer has the same question open.

## Rabbit-holes

- **The full class diagram.** A handful of properties occur on nearly every class and turn it into a
  hairball. Factoring them into a shared base class or a note is worth one attempt; if it is still
  unreadable, ship the hierarchy-only view and say so.
- **SHACL semantics.** The shapes are descriptive: `sh:minCount` only when every instance has the
  property, `sh:maxCount 1` only when none has more than one value, `sh:datatype`, `sh:class` or
  `sh:or` from the observed types, `sh:nodeKind sh:BlankNodeOrIRI` for untyped objects. Do not try
  to infer intended constraints.
- **Fuseki quirks.** `stain/jena-fuseki` rejects uploads unless `ADMIN_PASSWORD` is set, and
  `--file` loads only one file.

## No-gos

- No client-specific names, namespaces, IRIs, counts or outputs committed here: this repository is
  public.
- No API or UI integration of the CLI in this change.
- No changes to the library from this repository; library work happens in the library.
- No modernisation of the repository tooling (Poetry, Ruff, mypy, import-linter); that is its own
  change.
- No profiling queries of our own that duplicate the library (DEC-4).
- No own HTML report; the library's HTML report is the HTML output.

---

## What Changes

- A new `profile` CLI command in the `fingerprinter` package.
- `upload_file_to_dataset` and the Fuseki adapter can load a file into a named graph.
- New renderers for the outputs the library does not provide (DEC-5): report, PlantUML, SHACL,
  prefix map.
- `requirements/` moves to the upgraded `rdf-fingerprinter`; the existing API/UI is checked
  against it.

## Capabilities

### New Capabilities
- `data-profiling`: profile an RDF dataset from an endpoint or files, and write the JSON
  fingerprint, a prefixed report, PlantUML class diagrams, descriptive SHACL and the prefix map.

### Modified Capabilities

## Impact

- Code: `fingerprinter/entrypoints/cli/` (new), `fingerprinter/services/`, and
  `fingerprinter/adapters/sparql_adapter.py` (named-graph upload).
- Dependencies: the upgraded `rdf-fingerprinter`; possibly the Python version of the Docker images
  (DEC-6).
- Systems: Fuseki for file input (`make start-services`).
- The prototype in `site/` stays git-ignored and is not ported as is.
