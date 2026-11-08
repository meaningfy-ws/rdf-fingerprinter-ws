# Acceptance demo — upgrade stage 4 (infra and delivery) and the EPIC's success measure

> Run by the leader on 2026-11-08 from a clean clone; **validation is the developer's** (sign-off at
> the end). Change `upgrade-fingerprinter-library`, task 4.6.

## How it was run

`git clone --branch feat/upgrade-stage-4-infra` into `temp/clean`; `cp infra/.env.example
infra/.env` with the three `change-me` values replaced by random ones; `make install`; `make up`.
Fuseki of the stack holds a dataset `demo`: `continents-source-ap.rdf` in the default graph,
`courts-source-ap.rdf` and `pitfall-untyped-class.ttl` in two named graphs.

## Results against the success measure

| Clause | Result |
|---|---|
| Endpoint job from the API (`http://fuseki:3030/demo/sparql`) | `completed`; `html`, `json`, `shacl`, `puml`, `svg`, `pattern`, `shex`, `pitfalls` and `zip` each answer 200; the zip holds 48 files |
| File job from the API (`treaties-source-ap.rdf`) | `completed`; every format and the zip answer 200 |
| Endpoint job from the UI, two named graphs chosen with "Load graphs" | Done without a reload; the class diagram shows on its Job page |
| File job from the UI (`continents-source-ap.rdf`) | Done without a reload |
| Pitfall findings in `main.html` | present (the untyped-class check fires on the pitfall graph) |
| Unreachable endpoint (`http://unreachable.invalid/sparql`) | `failed`, reason "cannot reach endpoint …" |
| Every port | published on `127.0.0.1` only (API 4020, UI 8020, Fuseki 3030, Flower 5557, …) |
| No 0.3 / 3.8 / `requirements/` reference | `git grep` outside the change history finds none |
| `make check-all`, container tests in CI on Python 3.13 | green on the stage PR |

## Found and fixed during the run

- `make check-env` refused a filled `.env`: it matched the template's comment naming `change-me`.
  Only setting lines are checked now.
- Every download answered 500: a relative `RDF_FINGERPRINTER_REPORTS_DB` was resolved by Flask
  against the API package. `Settings` resolves both folders; a unit test pins it.
- `make up` reuses images built earlier on the machine; the README says to `make rebuild` after
  pulling.

- [x] Accepted by the developer (2026-11-08): "Accept all three".
