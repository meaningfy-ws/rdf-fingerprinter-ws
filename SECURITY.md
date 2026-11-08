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

### Outgoing traffic of the worker (SSRF)

The service has no login, and the worker fetches **any** http(s) SPARQL endpoint URL a client submits.
A client can therefore make the worker reach whatever the worker's network reaches: the other
containers (Fuseki, Redis), the host, and cloud metadata addresses. The service refuses only URLs
that carry a user name or password.

Restrict the worker's egress at the network level; Docker Compose cannot do it alone. For instance:

- block the private, loopback and link-local ranges (including `169.254.169.254`) from the worker,
  allowing only Redis, Fuseki and PlantUML inside the stack;
- or send the worker's outgoing traffic through an egress proxy that allows only the endpoints you
  expect;
- or run the stack in a network that has no route to your internal network.

The API and the UI have no authentication: put them behind your own access control and TLS, and set
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
- Redis, Fuseki, PlantUML and Flower are published on `127.0.0.1` only. Flower has no login: do not
  expose it.
