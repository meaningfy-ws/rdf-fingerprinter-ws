# Acceptance demo — UI stage 2 (Job page, report and diagrams)

> Prepared by the leader on 2026-11-08; **validation is the developer's** (sign-off at the end).
> Change `modernise-user-interface`, task 2.4.

## Where

The demo stack runs from `develop` once this stage is merged: UI http://localhost:8020, API
http://localhost:4020/ui (Swagger), Fuseki, Redis and the PlantUML server in Docker.

## What to try

1. Start an endpoint job (`http://localhost:33040/demo/sparql`) and open it from Jobs when it is
   Done. The header shows the source, the badge, the start time, the duration and the short id.
2. **Report** tab: the library's report in the page, with its pitfall section; "Open in new tab".
3. **Class diagram** tab: the whole-model diagram first; the picker lists each vocabulary
   ("Vocabulary: skos", split modules as "(part n)"); "Download SVG".
4. **Downloads** tab: every format with its description and file count, and "Download all (.zip)".
5. Stop the PlantUML container and run a job: it ends "Done with warnings", the warnings panel
   ("Some parts could not be produced (n)") names each diagram that could not be drawn, the Class
   diagram tab says why, and the other formats download.
6. A job against `http://unreachable.invalid/sparql`: "Failed" with the reason, no tabs.

## Checked by the agents

- `make check-all`: 558 tests; `make test-containers`: 68 tests, green twice.
- Browser journey "open a job's report, diagram and a download"; axe-core WCAG 2.2 AA on the
  Job page's three tabs and a failed job, light and dark, and at 360 px; no external asset.
- Five-lens review, findings fixed (design.md, "Stage-2 review", S2-1 to S2-6).

- [ ] Accepted by the developer.
