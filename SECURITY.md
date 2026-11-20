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
The API does too: `GET /endpoint-graphs` lists the named graphs of an endpoint the client names. The
service itself refuses only URLs that carry a user name or password.

The stack in `infra/` enforces the egress limit at the network level:

- the `app`, `work` and `monitor` networks are `internal` (no route out); the API and the worker have
  no route to the Internet or the host, and Redis, Fuseki and PlantUML have none at all;
- the API and the worker send their requests through the Squid egress proxy (`HTTP_PROXY`,
  `HTTPS_PROXY`), which refuses loopback, private, link-local, shared and unspecified addresses
  (IPv4 and IPv6) by the address the name resolves to, so `169.254.169.254`, `127.0.0.1`, `redis`
  and `fingerprinter-api` are all refused and the job fails; every other destination and port is
  allowed, since users bring their own endpoints;
- the worker shares no network with Flower or the API.

Residual risks:

- a user URL naming `fuseki` or `plantuml` bypasses the proxy (`NO_PROXY`, which the stack's own
  traffic needs): Fuseki's admin interface needs the password, and PlantUML runs in `SANDBOX`;
- Redis has no password: it is reachable only on the internal `work` and `monitor` networks (and on
  loopback with `make up-dev` or `make up-deps`);
- a host or cloud firewall is further advice, not shipped: on a Docker host, restrict the egress of
  the stack's networks in the `DOCKER-USER` chain, and keep the cloud metadata address unreachable
  from the host's containers.

If you run the images outside this compose file, restrict the egress of the worker **and** the API
yourself (a proxy like this one, a network without a route to your internal network, or firewall
rules), and keep Flower unreachable from both.

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

- Settings and secrets live in `infra/.env`, which is git-ignored; `make init-env` writes it from
  `infra/.env.example` with a random value for every `change-me` and refuses to overwrite one. Each
  container receives only its own secrets: the API its secret key and the Fuseki credentials, the UI its
  secret key, the worker the Fuseki credentials, Flower none. An existing Fuseki volume keeps the admin
  password it was created with.
- Never commit a `.env`. The `docker/.env` that earlier versions committed held keys that are
  **burned**; do not reuse any value from the repository's history.
- The images carry no `.env`, data or credentials, and run as a non-root user.
- The API and the UI (through the nginx edge proxy) and Flower are published on `127.0.0.1` only. Redis,
  Fuseki and PlantUML are published only by the development override (`make up-dev`, `make up-deps`),
  also on `127.0.0.1`. Flower has no login: do not expose it.
- Secret values use only letters and digits: `make` sources `infra/.env` as shell, and `make check-env`
  refuses a file that still holds `change-me`.
