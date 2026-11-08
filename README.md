# RDF Fingerprinter WS

A web service and UI that fingerprint an RDF file or a SPARQL endpoint with the
[`rdf-fingerprinter`](https://github.com/meaningfy-ws/rdf-fingerprinter) library: they guess the
application profile the data instantiates and write a report in several formats. Fingerprinting runs
as asynchronous jobs.

Documentation: the `docs/` Antora component (`make build-docs`); the developer runbook is
`docs/modules/ROOT/pages/develop/`.

## Install

Requires [uv](https://docs.astral.sh/uv/) (it fetches Python 3.13) and Docker.

```bash
make install      # uv sync: the service and its development tools
make check-all    # lint, type check, architecture, spec, docs and the tests
```

## Run the stack

```bash
cp infra/.env.example infra/.env     # then replace every "change-me" (letters and digits only)
make up                              # start the stack (builds the images the first time)
make logs                            # follow the logs
make down                            # stop it (the data volumes stay)
make rebuild                         # rebuild the images and start (up -d --build)
```

| Service | URL (default ports) | Role |
|---|---|---|
| `fingerprinter-ui` | <http://localhost:8020> | the web UI, a client of the API (localhost only) |
| `fingerprinter-api` | <http://localhost:4020> | the REST API (localhost only); Swagger UI at <http://localhost:4020/ui> |
| `fingerprinter-flower` | <http://localhost:5557> | Flower, a view of the Celery jobs (localhost only) |
| `fingerprinter-worker` | – | runs the fingerprinting jobs |
| `fuseki`, `redis`, `plantuml` | localhost only | temporary datasets of uploaded files, the Celery broker, the class diagrams |

`infra/.env` (git-ignored) holds the settings and the secrets; `infra/.env.example` lists every one.
The images are built from the targets `api`, `ui` and `worker` of `infra/docker/Dockerfile` and published to
`ghcr.io/meaningfy-ws/rdf-fingerprinter-ws-{api,ui,worker}` on each release.

To work on one service on the host, run `make up-deps` (only Redis, Fuseki and PlantUML), then
`make run-api`, `make run-ui` and `make run-worker`. Do not run them next to the full stack: both would
take jobs from the same queue.

**Security.** The API and UI are published on `127.0.0.1` only and have no login; the worker and the
API fetch the endpoint URLs clients submit. See [SECURITY.md](SECURITY.md) before exposing the stack.

## The API

The authoritative contract is `fingerprinter/entrypoints/api/openapi/fingerprinter.yml`; the table
below is a summary, and the running API serves the contract at `/ui`. Errors are `application/problem+json`.

| Method and path | Does | Answers |
|---|---|---|
| `POST /fingerprint-sparql-endpoint` | start a job for a SPARQL endpoint (JSON: `sparql_endpoint_url`, optional `graphs`) | `202` `{"task_id"}`; `400`, `503` |
| `POST /fingerprint-file` | start a job for an uploaded RDF file (multipart field `data_file`) | `202` `{"task_id"}`; `413`, `415`, `503` |
| `GET /reports` | list the job records | `200` |
| `GET /reports/{uid}` | one job record | `200`; `404` |
| `DELETE /reports/{uid}` | delete a job and its report | `200`; `404`, `409` while the job is queued or running |
| `GET /reports/{uid}/{format}` | download a format (`html`, `json`, `shacl`, `puml`, `svg`, `pattern`, `shex`, `pitfalls`, `zip`); a format of several files comes as a zip | `200`; `400`, `404` |
| `GET /reports/{uid}/{format}/{file}` | download one file of a format | `200`; `404` |
| `DELETE /remove-reports` | delete every job and report | `200` |
| `GET /tasks/active` | the jobs that are queued or running | `200` |
| `GET /tasks/{task_id}` | the state of a job: `queued`, `running`, `completed`, `completed_with_failures`, `failed`, `cancelled` | `200`; `404` |
| `DELETE /tasks/{task_id}` | cancel a queued or running job | `200`; `404`, `409` when it has finished |

Examples (default port; replace the placeholders):

```bash
# a SPARQL endpoint; "graphs" is optional
curl -X POST localhost:4020/fingerprint-sparql-endpoint \
  -H 'Content-Type: application/json' \
  -d '{"sparql_endpoint_url": "<sparql-endpoint-url>", "graphs": ["<graph-1>"]}'

# a file
curl -X POST localhost:4020/fingerprint-file -F 'data_file=@<path-to-file>'

# the job records, one job, one format of its report
curl localhost:4020/reports
curl localhost:4020/tasks/<task_id>
curl -OJ localhost:4020/reports/<uid>/html

# cancel a running job, delete a finished one, delete everything
curl -X DELETE localhost:4020/tasks/<task_id>
curl -X DELETE localhost:4020/reports/<uid>
curl -X DELETE localhost:4020/remove-reports
```

## The UI

Open <http://localhost:8020>: the console lists the jobs and starts new ones (an endpoint with an
optional graph choice, or a file); a job's page shows the report, the class diagram and the
downloads.

## Contributing

We adhere to the [Apache code of conduct](https://www.apache.org/foundation/policies/conduct).
Please discuss a change with the maintainers (an issue is fine) before making it, and follow the
developer runbook. See [CHANGELOG.md](CHANGELOG.md) for what changed.

## Licence

GNU GPLv3 (see [LICENSE](LICENSE)). Powered by [Meaningfy](https://github.com/meaningfy-ws).
