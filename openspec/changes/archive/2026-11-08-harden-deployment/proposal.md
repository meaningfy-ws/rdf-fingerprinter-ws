# EPIC: Harden the deployment

> Golden thread: follows `upgrade-fingerprinter-library` (archived; its deferred items: egress
> restriction #35, per-service secrets) and `modernise-user-interface` (archived; S3-5: the API
> also fetches user-given URLs). Seed: `inputs/seed.md` (the developer, 2026-11-08).

## Appetite

**SMALL**. Compose networks, two off-the-shelf containers (an egress proxy and an edge proxy), the
settings' secret checks, two make targets, the licence and the docs. No new service behaviour.

## Why

The worker and the API fetch any URL a user gives them, and in the `infra/` stack they can reach
every container, the host and cloud metadata addresses: an unauthenticated SSRF into the stack.
Every container also receives every secret, so one compromised container leaks them all. The
licence files disagree.

## Solution outline

When this is done, the API, UI and worker have no route out of the stack except an egress proxy
that refuses loopback, private, link-local and shared addresses; Redis, Fuseki and PlantUML have
no route out at all; the worker cannot reach Flower or the API; the UI and API are reached through
an edge proxy published on `127.0.0.1`. Each container holds only the secrets it uses. `make
init-env` writes `infra/.env` with random secrets; `make down` works without it. The licence is
Apache-2.0 everywhere.

**Success measure**: on the stack from a clean clone (`make init-env`, `make up`), a job against
`http://169.254.169.254/`, `http://redis:6379/` or `http://127.0.0.1:4020/` fails with a refusal,
while a job against a public endpoint reached through the proxy, and a file job, complete; `docker
compose exec` shows the worker holds no Flask secret key; the infra unit tests pin the networks,
the proxy settings and the secrets per service.

## Key decisions

- **DEC-1 Networks.** Four compose networks: `edge` (a normal bridge: the edge proxy, Flower, the
  egress proxy), `app` (internal: edge proxy, UI, API), `work` (internal: API, worker, Redis,
  Fuseki, PlantUML, egress proxy), `monitor` (internal: Redis, Flower). A container on internal
  networks only has no route out. Rejected: host firewall rules only (outside the repository, not
  testable here; kept as advice in `SECURITY.md`).
- **DEC-2 Egress proxy.** Squid (`ubuntu/squid`, pinned) on `work` and `edge`, refusing
  destinations in 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16,
  100.64.0.0/10, 0.0.0.0/8 and their IPv6 counterparts (::1, fc00::/7, fe80::/10); any port is
  allowed otherwise (SPARQL endpoints use many). The API and worker get `HTTP_PROXY`/`HTTPS_PROXY`
  and `NO_PROXY=fuseki,plantuml` (the library's `urllib` and `requests` honour them). Residual,
  documented: a user URL naming `fuseki` or `plantuml` bypasses the proxy; Fuseki's admin needs the
  password and PlantUML runs `SANDBOX`. Rejected: an allow-list of endpoints (users bring their own);
  smokescreen (no maintained image).
- **DEC-3 Edge proxy.** nginx (`nginx:*-alpine`, pinned) on `edge` and `app` publishes the UI and the
  API on `127.0.0.1`; neither the UI nor the API is on a network with a route out. Flower stays
  published directly (it fetches no user URL).
- **DEC-4 Development access.** `infra/compose.dev.yaml` publishes Redis, Fuseki and PlantUML on
  `127.0.0.1` for `make up-deps` and the `run-*` targets, and for loading demo data. Not used by
  `make up`.
- **DEC-5 Secrets per service.** `Settings` no longer requires both Flask keys; `bootstrap.api_app()`
  requires the API key and `ui_app()` the UI key. Compose drops `env_file` and gives each service
  its variables by name: API key to the API, UI key to the UI, Fuseki credentials to the API, the
  worker and Fuseki.
- **DEC-6 Make targets.** `make init-env` writes `infra/.env` from the example with random secrets
  and refuses to overwrite one; `make down` works without `infra/.env` (it names the project).
- **DEC-7 Licence.** Apache-2.0: `LICENSE`, README and `pyproject.toml` agree.

## Rabbit-holes

- Squid's default config allows `CONNECT` only to 443; SPARQL over https on other ports needs it
  opened, without opening the refused ranges.
- Docker publishes no port for a container on internal networks only; that is why DEC-3 adds an
  edge proxy.

## No-gos

- No authentication of the API or UI, no TLS (a deployment's own proxy does that).
- No host firewall rules shipped (advice only).
- No change to the service's behaviour or API.

---

## What Changes

- `infra/compose.yaml`: networks, the egress and edge proxies, per-service environment;
  `infra/compose.dev.yaml`; `infra/proxy/squid.conf`, `infra/edge/nginx.conf`.
- `fingerprinter/config.py`, `fingerprinter/bootstrap.py`: secret keys required per app.
- `Makefile`: `init-env`, `down` without `.env`, `up-deps` with the dev override.
- `LICENSE`, README, `SECURITY.md`, CHANGELOG, docs.

## Capabilities

### New Capabilities
- `deployment-security`: the stack's network isolation, egress filtering and per-service secrets.

### Modified Capabilities

## Impact

- Systems: two more containers (egress proxy, edge proxy).
- Operators: `infra/.env` is created by `make init-env`; host ports unchanged.
