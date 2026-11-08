---
kind: elicitation record (secondary; superseded by proposal.md, never groomed)
---

# Elicitation — modernise the user interface

Answers the developer gave on 2026-11-08 while shaping this EPIC, in the order asked. Each
recommendation offered is marked; the answer is what the developer chose.

## Origin

- The developer's opening request named two EPICs: adopt the latest `rdf-fingerprinter`
  (`upgrade-fingerprinter-library`, shaped and merged in PR #24), and "improving and modernising
  the user interface" (this one).
- **Next.js or Flask (asked while shaping the upgrade).** Answer given: Flask (Jinja + htmx) covers
  a job console; Next.js pays off for an interactive explorer of fingerprints. **Chosen: keep Flask
  for now.**
- Then: "shape the epic, then we implement both".

## The UI today (seen on `develop` at `c311ba5`)

Materialize 1.0 (unmaintained since 2018) and jQuery from CDNs, Google Fonts icons; three pages
(endpoint form, file form, active Celery tasks) and a report table with html/json/zip buttons;
delete and cancel are `GET` links with no confirmation; no live state, no failures shown.

## Round 1

| Question | Recommended | Chosen |
|---|---|---|
| What the UI lets a user do | Job console + report viewer | **Job console + report viewer** |
| Front-end inside Flask | Jinja + htmx, vendored assets, no build | **Jinja + htmx, vendored assets** |
| How progress shows | htmx polling | **htmx polling** |
| Named-graph picker on the endpoint form | No, free-text graphs | **Yes, via a library capability** |

The library lists named graphs internally (`Run.named_graphs()`, query `Q0`) but has no public
call; filed as `meaningfy-ws/rdf-fingerprinter#63`.

## Round 2

| Question | Recommended | Chosen |
|---|---|---|
| PlantUML output in the viewer | Download only | **Render via a PlantUML container** |
| UI tests | Flask test client + a few Playwright journeys | **Flask test client + a few Playwright** |
| Look and feel | Meaningfy-neutral, light/dark, WCAG AA | **Meaningfy-neutral, light/dark** |
| Order of the two EPICs | Upgrade fully, then UI | **Upgrade fully, then UI** |

## Leader's choices (the developer may overrule)

- The class diagram is rendered once, by the worker, when the job runs, and stored with the report
  as SVG (it travels in the zip); a rendering failure is listed as a job failure, not a job error.
- The report page (`main.html`) is shown in a sandboxed frame (scripts allowed, no same-origin):
  it holds an inline script and text taken from the profiled data.
- Pitfall findings are seen in the report page, where the library already puts them; the UI does
  not re-render the pitfalls file.
- Destructive actions (delete, cancel) become `POST` forms with a confirmation step.

## Found while building the upgrade (2026-11-08)

- The library's `puml` output is several files: `diagram-default.puml` and one
  `diagram-default--<module>.puml` per namespace module (rdf-fingerprinter 3.6.0). DEC-6 assumed one
  `diagram.puml`; the PLAN must decide which diagram(s) the viewer renders.
- `list_named_graphs` was released in rdf-fingerprinter 3.6.0 (#63), so stage 3 of this EPIC is no
  longer blocked.
