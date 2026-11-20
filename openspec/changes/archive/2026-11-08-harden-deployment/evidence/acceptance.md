# Acceptance — harden-deployment (2026-11-08)

Run by the leader from a clean clone of `feat/hardening`: `make init-env`, `make rebuild`.

| Check | Result |
|---|---|
| File job (`treaties-source-ap.rdf`) | `completed`, eight formats; `html` and `zip` answer 200 through the edge |
| Job against `http://169.254.169.254/sparql` | `failed`, refused by the egress proxy |
| UI on `127.0.0.1:8020` through the edge | 200 |
| Worker environment | no Flask secret key |

The implementer's fuller run (design "As built"): `redis:6379`, `fingerprinter-api:4020` and
`127.0.0.1:4020` refused (squid `TCP_DENIED/403`); public https and http through the proxy; no
direct route out; `fuseki` reached via `NO_PROXY` under `make up-dev`; `make init-env` refuses a
second run; `make down` without `.env`.

Validation: the developer asked to conclude the change ("conclude the epic asap", 2026-11-08).
