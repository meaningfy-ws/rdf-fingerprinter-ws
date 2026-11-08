---
kind: elicitation record (secondary; superseded by proposal.md, never groomed)
---

# Elicitation — data profiling tool

Answers given while shaping, against the open decisions in `handover.md`. Generic only: this
repository is public.

## Decided

- **Form** (handover decision 1): a CLI entrypoint inside the `fingerprinter` package
  (`entrypoints/cli`, on `click`, already a dependency). Profiling and rendering live in
  services/adapters so the API could call them later. API/UI integration is a no-go for this change.
- **Namespace classification** (handover "must change"): inferred by default. A namespace is schema
  when it holds classes or predicates, and data when it holds only subjects or objects. Prefixes for
  common vocabularies (rdf, rdfs, owl, xsd, skos, dcterms, dc, foaf, prv, sh) are built in; the rest
  get generated names. An optional override file sets prefixes, roles and data-IRI patterns (for
  example `{base}/{Collection}/{id}`, one prefix per collection).
- **Input and triplestore** (handover decision 2): Fuseki, not rdflib. The CLI takes either
  `--endpoint URL` (an existing SPARQL endpoint), or `--data FILE [--ontology FILE]`. The files are
  loaded into a temporary Fuseki dataset by reusing `services/handlers.upload_file_to_dataset`,
  extended so the ontology goes to a named graph. File input needs a running Fuseki
  (`make start-services`).
- **Relation to the library** (handover decision 3): the library must be used. The owner upgrades it
  so this tool can rely on it (speed, JSON output, named ontology graph, no `logging.conf`, current
  Python). The EPIC is parked until then.

## Still open

- Which outputs the upgraded library provides, and which this repository renders.
- Python version (handover decision 4), now tied to the upgraded library.
- Treatment of instance IRIs used as predicates.
- The full diagram: factor out the common properties, or leave it out of scope.
- Output location and file naming.
- Test scenarios the EPIC must prove.
- Appetite (proposed: MEDIUM).
