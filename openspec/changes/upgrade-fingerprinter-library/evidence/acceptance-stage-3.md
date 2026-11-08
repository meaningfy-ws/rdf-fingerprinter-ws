# Acceptance demo — stage 3 (Outputs and API)

> Prepared by the leader on 2026-11-08 from a local run of the real processes; **validation is the
> developer's** (sign-off at the end). Change `upgrade-fingerprinter-library`, task 3.7.

## Stack

Branch `feat/upgrade-stage-3-outputs`, rdf-fingerprinter 3.6.0, Python 3.13:
`stain/jena-fuseki:5.1.0` and `redis:7-alpine` in Docker; the API
(`gunicorn -k uvicorn.workers.UvicornWorker 'fingerprinter.bootstrap:api_app()'`, port 4020), the
worker (`celery -A fingerprinter.bootstrap:celery_app worker`) and the UI
(`gunicorn 'fingerprinter.bootstrap:ui_app()'`, port 8020) as local processes. The endpoint was a
Fuseki dataset holding `continents-source-ap.rdf` in its default graph and
`pitfall-untyped-class.ttl` in `http://example.org/pitfalls`.

## Observed

| Check | Result |
|---|---|
| Endpoint job from the API (`POST /fingerprint-sparql-endpoint`) | `202`, then `completed` in 5.5 s; formats `html json shacl puml pattern shex pitfalls` |
| Its eight downloads (`GET /reports/{id}/{format}`) | all `200`; `html` text/html, `json` application/json; `shacl`, `shex`, `pitfalls`, `puml`, `pattern` as zips (two graphs → one file per graph); `zip` 23.6 kB |
| Pitfall findings in the report | `main.html` names `p34_untyped_class`; the pitfalls output holds it |
| File job from the API (`POST /fingerprint-file`, `treaties-source-ap.rdf`) | `202`, then `completed`; one graph, so `shacl` text/turtle, `shex` text/shex, `pitfalls` text/tab-separated-values as single files |
| File job cleanup | Fuseki lists only the demo dataset (no `fp-<id>`); the upload folder is empty |
| Unreachable endpoint | `failed`, reason "cannot reach endpoint http://unreachable.invalid/sparql: … (after 2 retries)" |
| UI report list | the endpoint job shows eight links (seven formats + zip); the failed job shows its state and reason |
| UI download (`/reports/{id}/puml`) | `200`, application/zip, `attachment; filename=<id>-puml.zip` |
| File job from the UI form | accepted, redirected to the list |

Job ids: endpoint `3cbe1c65-4521-4701-925f-7799cd5763c2`, file `bb492693-842e-4480-be64-3f8f96f480d2`, unreachable `8af7b81c-e8f2-4387-95b6-ae732e302f2d`.

## For the developer

The stack is still running: open http://localhost:8020 (UI) and http://localhost:4020/ui (Swagger).
Start a job of your own, download a format, and reply with your verdict.

- [ ] Accepted by the developer (date, remarks):
