# package-boundaries Specification

## Purpose
The layering of the `fingerprinter` package (domain, services, adapters, entrypoints, bootstrap) and the rule that only one adapter imports the library, enforced by import-linter. From `upgrade-fingerprinter-library` (archived 2026-11-08).
## Requirements
### Requirement: Layers import in one direction
The `fingerprinter` package SHALL be organised in the layers `domain`, `services` (with their ports),
`adapters` and `entrypoints` (`api`, `ui`, `worker`), under a composition root `bootstrap`. Imports
SHALL go `bootstrap → entrypoints | adapters → services → domain`; `entrypoints` and `adapters` SHALL
NOT import each other; `fingerprinter.config` SHALL be imported only by `bootstrap`. `make
check-architecture` SHALL enforce this with import-linter (DEC-8).

#### Scenario: A forbidden import fails the check
- **GIVEN** a module in `fingerprinter.services` that imports `fingerprinter.adapters`
- **WHEN** `make check-architecture` runs
- **THEN** it fails and names the forbidden import

#### Scenario: The delivered code passes
- **WHEN** `make check-architecture` runs on the delivered code
- **THEN** every contract passes

### Requirement: The domain is free of frameworks
`fingerprinter.domain` SHALL NOT import `flask`, `connexion`, `celery`, `requests` or `fingerprint`.

#### Scenario: A framework import in the domain fails the check
- **GIVEN** a module in `fingerprinter.domain` that imports `flask`
- **WHEN** `make check-architecture` runs
- **THEN** it fails and names the forbidden import

### Requirement: The UI is a client of the API
`fingerprinter.entrypoints.ui` SHALL import no other `fingerprinter` module; it SHALL reach the
service only through the HTTP API.

#### Scenario: A service import in the UI fails the check
- **GIVEN** a module in `fingerprinter.entrypoints.ui` that imports `fingerprinter.services`
- **WHEN** `make check-architecture` runs
- **THEN** it fails and names the forbidden import

### Requirement: One adapter calls the library
Only `fingerprinter.adapters.fingerprint_library` SHALL import the `fingerprint` library.

#### Scenario: A second importer of the library fails the check
- **GIVEN** a module `fingerprinter.adapters.fuseki` that imports `fingerprint`
- **WHEN** `make check-architecture` runs
- **THEN** it fails and names the forbidden import

