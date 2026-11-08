---
kind: analysis brief (secondary; superseded by proposal.md, never groomed)
---

# UI analysis — 2026-11-08 (after upgrade stage 3)

The developer, on seeing the stage-3 UI: "include a proper revamping of the ui, add a modern design
and clean ui, make it look slick, and also the labels are not very intuitive, improve them, analyse
first". Analysis of the running UI (templates, forms, messages), then: "go ahead" with the plan
(UI EPIC next, before upgrade stage 4; mockups first).

## Look and build
- Materialize 1.0 (unmaintained since 2018), jQuery and Google icon fonts from CDNs.
- Purple navbar, grey footer, default blue/red buttons, no hierarchy.
- The navigation is hidden below desktop width (`hide-on-med-and-down`) with no mobile menu.
- Eight download buttons plus "Remove" per row, all alike.

## Flows
- Two lists (reports, active tasks); nothing updates without a reload.
- Delete and cancel are plain GET links with no confirmation.
- No report is readable in the page; every format is a download.
- The file page's "Reset form" goes to the endpoint page (bug).

## Labels (today → proposed)
| Where | Today | Proposed |
|---|---|---|
| Tab title | "RDF Fingeprinter" (typo) | "RDF Fingerprinter" |
| Meta | `content="RDF-Differ"` | the right name |
| Navigation | SPARQL Endpoint · File · List active tasks | Jobs · New job (From an endpoint / From a file) |
| Home title | Fingerprinting reports | Jobs |
| Columns | ID · source · created at · state · Actions · Remove | Source · Started · Status · Outputs · row menu |
| ID | full UUID as row header | hidden; short id on the job page |
| Started | raw ISO UTC | relative ("5 min ago"), exact local time on hover |
| Status | queued, running, completed_with_failures, failed, cancelled | Queued · Running… · Done · Done with warnings · Failed · Cancelled |
| Downloads | Get html/json/shacl/puml/pattern/shex/pitfalls, Get all files | Report · Profile (JSON) · SHACL shapes · Class diagram (PlantUML) · Pattern schema · ShEx schema · Pitfalls (TSV) · Download all (.zip) |
| Row action | Remove | Delete… (asks first) |
| Cancel | Stop task | Cancel job… (asks first) |
| Endpoint form | Endpoint URL · Graphs "Separate them through spaces. example: graph1 graph2" | SPARQL endpoint URL (with example) · Named graphs (optional), "Load graphs" picker, "leave empty to profile every graph" |
| File form | Data file · Browse · Upload file | RDF file, accepted types and size limit listed |
| Submit | Fingerprint SPARQL Endpoint / Fingerprint File | Start fingerprinting |
| Messages | fingerprinting successfully started/deleted | Job started. / Report deleted. |
| Errors | "Status: 400. Title: Bad Request Detail: …" | one plain sentence |
| Failures | raw library strings | "Some measurements failed (n)", expandable |
