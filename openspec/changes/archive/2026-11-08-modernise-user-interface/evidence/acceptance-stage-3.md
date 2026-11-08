# Acceptance demo — UI stage 3 (Graph picker) and the EPIC's success measure

> Prepared by the leader on 2026-11-08; **validation is the developer's** (sign-off at the end).
> Change `modernise-user-interface`, task 3.3.

## Where

UI http://localhost:8020, API http://localhost:4020/ui. Demo endpoint
`http://localhost:33040/demo/sparql`: `continents` in the default graph, `courts` and `treaties`
in the named graphs `http://data.europa.eu/eli/graph/courts` and `.../treaties`.

## What to try (the success measure)

1. **New job** → paste the demo endpoint → **Load graphs**: two graphs listed. Tick both, start.
   Upload `tests/resources/treaties-source-ap.rdf` from **From a file**.
2. On **Jobs**, both move to Done without a reload.
3. Open each: the report in the page, the class diagrams (whole model, then each vocabulary), the
   downloads; download one format and the zip.
4. A job against `http://unreachable.invalid/sparql`: Failed, with its reason. **Load graphs** on
   it says the endpoint could not be reached, and the job can still be started without graphs.
5. Change the URL after ticking graphs and start: "These graphs belong to another endpoint."
6. Cancel a running job and delete a report, each after the confirmation.

Screenshots: `docs/modules/ROOT/pages/index.adoc` (`ui-*.png`).

## Checked by the agents

- `make check-all`: 599 tests; `make test-containers`: 72 tests (before the charset fix; re-run in CI).
- Browser journeys incl. loading graphs (focus kept; failure sentence; job still starts); axe-core
  WCAG 2.2 AA on every page, light and dark, 360 px; no external asset.
- Five-lens review, findings fixed (design.md, "Stage-3 review", S3-1 to S3-8). Library gaps filed:
  `meaningfy-ws/rdf-fingerprinter#76` (no overall query deadline or size limit) and `#77`
  (`list_named_graphs` error contract).

- [x] Accepted by the developer (2026-11-08): "Accept all three".
