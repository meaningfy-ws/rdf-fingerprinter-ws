---
kind: design reference (secondary; superseded by proposal.md, never groomed)
---

# Approved mockups — 2026-11-08

Clickable mockups: https://claude.ai/artifact/5YfXhAHoTinso86FvHbdEB (private to the developer).
The developer: "i like the ui, proceed implementing it".

1. **Jobs** — one list: Source (name + kind line), Started (relative, exact time on hover), Status
   badge + one-line note, Outputs ("Open report", "Download all (.zip)"), a ⋯ menu; filters All ·
   In progress · Finished · Failed; "Updates by itself while a job is queued or running."; header
   with the product mark, "Jobs" and a primary "New job" button; light and dark themes.
2. **New job** — tabs "From an endpoint" / "From a file"; "SPARQL endpoint URL" with help text and
   "Load graphs"; "Named graphs (optional)" checkboxes, "Leave all unticked to profile every graph,
   including the default graph."; file drop zone listing the accepted types and the size limit;
   "Cancel" and "Start fingerprinting"; a "What you get" panel explaining each output.
3. **Job and report** — title = source, status badge, meta line (kind, graphs, started, took, short
   id); "Delete…"; a collapsible warning "Some measurements failed (n) — the report is complete apart
   from these."; tabs Report (the library's page in a sandboxed frame, "Open in a new tab"), Class
   diagram (picker: whole model, then each vocabulary; "Download SVG"), Downloads (one row per
   output: name, plain description, file or "n files (.zip)", "Download").
4. **Delete** — alert dialog "Delete this report?" naming the source, "This cannot be undone.",
   "Keep it" / "Delete report"; cancelling a job follows the same pattern ("Cancel this job?").

## Copy and colours (from the approved mockups, written out for the build)

Colours (light / dark): ground `#F6F7F9` / `#0F1115`; surface `#FFFFFF` / `#171A21`; text `#111827` /
`#E8EAF0`; muted text `#4B5563` / `#A3A9B8`; lines `#E5E7EB` / `#2A2F3A`; soft fill `#EEF1F6` /
`#232835`; accent `#2F5BEA` (text on it `#FFFFFF`); danger button `#B91C1C`.

Status badges (background, text), light / dark:

| Status | Light | Dark | Note under the badge |
|---|---|---|---|
| Queued | `#F3F4F6`, `#374151` | `#2A2F3A`, `#D1D5DB` | "Waiting for a worker" |
| Running… | `#DBEAFE`, `#1D4ED8` | `#1E2A4A`, `#9DB7FF` | "Fingerprinting" |
| Done | `#DCFCE7`, `#166534` | `#13301F`, `#86EFAC` | "Took <duration>" |
| Done with warnings | `#FEF3C7`, `#92400E` | `#3A2A10`, `#FCD34D` | "<n> parts could not be produced" ("1 part could not be produced") |
| Failed | `#FEE2E2`, `#991B1B` | `#3B1616`, `#FCA5A5` | the job's reason up to its first ": " or ". ", at most 80 characters (an ellipsis when cut); the full reason on the Job page |
| Cancelled | `#F3F4F6`, `#374151` | `#2A2F3A`, `#D1D5DB` | "Cancelled" |

Kind line under the source: "SPARQL endpoint · all graphs" or "SPARQL endpoint · <n> named graphs" ("1 named graph")
(chosen graphs); "RDF file".

Empty state (Jobs, no job at all): "No jobs yet." / "Start one from a SPARQL endpoint or an RDF
file." with "New job". Empty filter: "No jobs here." with "Show all".

Format names and descriptions (Downloads tab and "What you get"):

| Format | Name | Description |
|---|---|---|
| html | Report | The report page, to keep or share. |
| json | Profile (JSON) | Every measurement, for tools and scripts. |
| shacl | SHACL shapes | The structure the data has, as SHACL. |
| puml | Class diagram (PlantUML) | The model, and one diagram per vocabulary, as PlantUML text. |
| svg | Class diagram (SVG) | The same diagrams as pictures. |
| pattern | Pattern schema | A compact description for people and LLMs. |
| shex | ShEx schema | The structure the data has, as ShExC. |
| pitfalls | Pitfalls (TSV) | Modelling problems found, one per line. |
| zip | Download all (.zip) | Everything above in one archive. |
