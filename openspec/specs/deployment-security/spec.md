# deployment-security Specification

## Purpose
The stack's network isolation, egress filtering through a proxy that refuses internal addresses, and one set of secrets per container. From `harden-deployment` (archived 2026-11-08).
## Requirements
### Requirement: User-given URLs leave the stack only through the egress proxy
The API and the worker SHALL have no direct route out of the stack; their requests to user-given
URLs SHALL go through the egress proxy, which SHALL refuse loopback, private, link-local, shared
and unspecified addresses (IPv4 and IPv6). Redis, Fuseki and PlantUML SHALL have no route out
(DEC-1, DEC-2).

#### Scenario: A metadata address is refused
- **WHEN** a job fingerprints `http://169.254.169.254/sparql`
- **THEN** the job is `failed` and nothing was fetched from that address

#### Scenario: A service of the stack is refused
- **WHEN** a job fingerprints `http://redis:6379/sparql`
- **THEN** the job is `failed`

#### Scenario: A public endpoint is reached
- **WHEN** the worker fetches a public https URL
- **THEN** the request goes through the egress proxy and succeeds

### Requirement: The worker cannot reach Flower or the API
The worker SHALL share no network with Flower and SHALL reach the API only through the egress
proxy, which refuses it (DEC-1).

#### Scenario: Networks are pinned
- **WHEN** the infra tests read `infra/compose.yaml`
- **THEN** the worker is on `work` only, Flower on `monitor` and `edge`, and the UI and API on no
  network with a route out

### Requirement: Each container holds only its secrets
The API container SHALL hold the API secret key and the Fuseki credentials, the UI container the
UI secret key only, the worker the Fuseki credentials only; the API process SHALL refuse to start
without its key, the UI without its key, and the worker SHALL need neither (DEC-5).

#### Scenario: The worker holds no Flask key
- **WHEN** the infra tests read the worker's environment in `infra/compose.yaml`
- **THEN** it names neither secret key

#### Scenario: Each app needs only its key
- **GIVEN** an environment with only the UI secret key
- **WHEN** the UI app and the API app are built
- **THEN** the UI app starts and the API app stops naming the missing API key

