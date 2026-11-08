# Security policy

## Supported versions

Only the latest release and the `develop` branch receive security fixes.

## Reporting a vulnerability

Do not open a public issue. Report it privately through GitHub
([Security advisories](https://github.com/meaningfy-ws/rdf-fingerprinter-ws/security/advisories/new))
or by email to <hi@meaningfy.ws>. Include what you found, how to reproduce it and the version. We
acknowledge a report within a few working days and tell you when a fix is released.

A vulnerability in the `rdf-fingerprinter` library itself is reported in its own repository,
<https://github.com/meaningfy-ws/rdf-fingerprinter>.

## Deploying safely

### Outgoing traffic of the worker and the API (SSRF)

The service has no login, and the worker fetches **any** http(s) SPARQL endpoint URL a client submits.
The API does too: `GET /endpoint-graphs` lists the named graphs of an endpoint the client names. A
client can therefore make the worker and the API reach whatever their network reaches: the other
containers (Fuseki, Redis, Flower), the host, and cloud metadata addresses. The service refuses only
URLs that carry a user name or password.

Restrict the egress of the worker **and** the API at the network level; Docker Compose cannot do it
alone. For instance:

- block the private, loopback and link-local ranges (including `169.254.169.254`) from both, allowing
  only Redis, Fuseki and PlantUML (and, for the UI, the API) inside the stack;
- or send their outgoing traffic through an egress proxy that allows only the endpoints you expect;
- or run the stack in a network that has no route to your internal network.

Flower has no login and must not be reachable from the worker or the API either.

Known limit: the library applies a timeout to a request as a whole but not to each read, so an endpoint
that answers slowly, a few bytes at a time, can hold a request open
([meaningfy-ws/rdf-fingerprinter#76](https://github.com/meaningfy-ws/rdf-fingerprinter/issues/76)).

### Exposure of the API and the UI

The API and the UI have no authentication and are published on `127.0.0.1` only. Open them to a
network only behind a reverse proxy that adds access control and TLS, and set
`RDF_FINGERPRINTER_UI_SECURE_COOKIES=true` when the UI is served over HTTPS.

### PlantUML

The class diagrams are rendered by a PlantUML server built from profiled data. It runs with
`PLANTUML_SECURITY_PROFILE=SANDBOX`, so no diagram can make it read a file or fetch a URL; keep that
setting (`infra/compose.yaml`, and `tests/unit/test_plantuml_stack.py` guards it).

### Secrets

- Settings and secrets live in `infra/.env`, which is git-ignored; start from `infra/.env.example` and
  replace every `change-me`. Use long random values for the two secret keys and the Fuseki password.
- Never commit a `.env`. The `docker/.env` that earlier versions committed held keys that are
  **burned**; do not reuse any value from the repository's history.
- The images carry no `.env`, data or credentials, and run as a non-root user.
- The API, the UI, Redis, Fuseki, PlantUML and Flower are published on `127.0.0.1` only. Redis has no
  password: it is reachable only on the stack's network and on loopback. Flower has no login: do not
  expose it.
- Secret values use only letters and digits: `make` sources `infra/.env` as shell, and `make check-env`
  refuses a file that still holds `change-me`.
