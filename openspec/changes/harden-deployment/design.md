# Design: harden-deployment

> Derives from: EPIC `harden-deployment` (`proposal.md`, DEC-1 to DEC-7).

## Context

`infra/compose.yaml` today: one default network, every service `env_file: .env`, every port on
`127.0.0.1`. The library queries endpoints with `urllib.request.urlopen` (honours `http_proxy`,
`https_proxy`, `no_proxy`); the adapters use `requests` (same variables).

## Decisions (how)

- **H-1 Networks** (DEC-1). `edge` (bridge), `app`, `work`, `monitor` (`internal: true`).
  | Service | Networks |
  |---|---|
  | edge (nginx) | edge, app |
  | fingerprinter-ui | app |
  | fingerprinter-api | app, work |
  | fingerprinter-worker | work |
  | fingerprinter-flower | monitor, edge |
  | egress (squid) | work, edge |
  | redis | work, monitor |
  | fuseki, plantuml | work |
- **H-2 Squid** (DEC-2). `infra/proxy/squid.conf`: `acl blocked dst` with the DEC-2 ranges;
  `http_access deny blocked`; `http_access allow all` for the `work` subnet only (`acl stack src`
  of the network, or allow all since only `work` reaches it); `CONNECT` allowed to any port;
  no cache (`cache deny all`); access log to stdout. API and worker environment:
  `HTTP_PROXY=http://egress:3128`, `HTTPS_PROXY` the same, `NO_PROXY=fuseki,plantuml` (lower-case
  copies too, since `urllib` reads both).
- **H-3 nginx** (DEC-3). `infra/edge/nginx.conf`: two `server` blocks listening on the UI and API
  ports, `proxy_pass` to `fingerprinter-ui:<port>` and `fingerprinter-api:<port>`; `client_max_body_size`
  from the upload limit (512m default; the template uses `envsubst` through the image's
  `/etc/nginx/templates`); `proxy_read_timeout` above the UI's 75 s listing wait (120 s); forwarded
  headers. The edge publishes `127.0.0.1:${API_PORT}` and `127.0.0.1:${UI_PORT}`.
- **H-4 Dev override** (DEC-4). `infra/compose.dev.yaml` adds a `dev` bridge network and the
  loopback ports to Redis, Fuseki and PlantUML; `make up-deps` uses `-f compose.yaml -f
  compose.dev.yaml`; a `make up-dev` does the same for the full stack (demo data loading).
- **H-5 Secrets** (DEC-5). `Settings.api_secret_key`/`ui_secret_key` read with a default of `""`;
  `bootstrap.api_app()` and `ui_app()` raise the same missing-variable error `_required` raises
  today when their key is empty. Compose: an `x-settings` anchor of the non-secret variables
  (interpolated from `.env`), merged into each service with its own secret lines.
- **H-6 Make** (DEC-6). `init-env`: refuse if `infra/.env` exists; copy the example; replace each
  `=change-me` with `openssl rand -hex 32` (letters and digits only). `down`: `docker compose -p
  rdf-fingerprinter-ws down` (no `.env` needed).

## Error matrix

| Failure | Handling |
|---|---|
| Proxy refuses a destination (403 from squid) | the library raises (`PermanentError`/unreachable); the job is `failed` with the reason; `/endpoint-graphs` answers 502 |
| Egress proxy down | the same as an unreachable endpoint |
| Edge proxy down | UI and API unreachable on the host |
| `make init-env` with an existing `.env` | exits 1, file untouched |

## Verification

Unit: `tests/unit/test_infra_env.py` pins H-1 (each service's networks; internal flags), H-2 (proxy
variables on API and worker; the squid ranges), H-5 (the secrets each service names);
`tests/unit/test_bootstrap.py` / `test_config.py` pin H-5's per-app checks. Manual, recorded in
`evidence/acceptance.md`: the success measure on a clean clone.

## As built

Divergences from H-1 to H-6, found while verifying on the stack (Rule of Divergence):

| Design | As built | Why |
|---|---|---|
| H-3 `infra/edge/nginx.conf` | `infra/edge/default.conf.template`, mounted at `/etc/nginx/templates/default.conf.template` (the image renders it to `conf.d/default.conf`: `server` blocks only, no `events`/`http`) | a `.conf` with `${...}` is not valid nginx; the image's template mechanism needs the `.template` name |
| H-3 `proxy_pass` to `fingerprinter-ui:<port>` | the upstream is a variable with `resolver 127.0.0.11 valid=10s`; `proxy_request_buffering off` and `proxy_buffering off` | a restarted UI or API is found again; a 512 MB upload or a zip download is streamed, not spooled to the proxy's disk |
| H-2 `access log to stdout` (`access_log stdio:/dev/stdout`) | no log directive: the image's entrypoint follows `/var/log/squid/access.log` and `cache.log` onto the container output | the `proxy` user cannot open `/dev/stdout`/`/dev/stderr` (permission denied; Squid exits) |
| H-2 IPv6 counterparts | `::/128 ::1/128 fc00::/7 fe80::/10`; no `::ffff:0:0/96` | Squid reads `::ffff:0:0/96` as `0.0.0.0/0` (every IPv4 address) and warns; IPv4-mapped literals are normalised to IPv4, so the IPv4 ranges cover them |
| H-2 `dns_v4_first`, `via off` | not set | `dns_v4_first` is obsolete in the pinned image (Squid 6.13 under tag `6.6-24.04_beta`); `via off` only warns |
| H-2 `allow all` for the `work` subnet only | `http_access allow all` after the `deny blocked`; the proxy is on `work` and `edge`, published nowhere | compose subnets are dynamic; nginx and Flower on `edge` can use the proxy too, and its denials apply to them |
| H-5 `x-settings` anchor | `x-settings` (non-secret settings), `x-egress` (proxy variables) and `x-fuseki-credentials` anchors, merged per service; Flower names only the Redis location and its port | each container holds only what it uses |
| H-4 | `make up-deps` also uses the override (it publishes the three on `127.0.0.1`) | the `run-*` targets need the loopback ports |

Known consequences, documented in `README.md`/`SECURITY.md` or reported:

- an existing `fuseki` volume keeps the admin password it was created with, so `make init-env` on an
  older install needs the old password kept, or the volume removed;
- a refused URL fails the job with Squid's HTML 403 page in the reason (the library's excerpt of the
  response); the refusal is clear, the reason is noisy.
