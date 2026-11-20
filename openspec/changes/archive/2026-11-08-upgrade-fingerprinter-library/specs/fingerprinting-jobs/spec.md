## ADDED Requirements

### Requirement: Start a job for a SPARQL endpoint
The service SHALL accept a request to fingerprint a SPARQL endpoint, given an `http` or `https` URL
and an optional list of graph IRIs, and SHALL answer with the id of a queued job. It SHALL reject a
request whose URL is missing, not `http`/`https`, or carries a user name or password with a `400`
problem response, before any job is queued (upgrade-fingerprinter-library DEC-5; design R2-1: job
records are readable by every client).

#### Scenario: A valid endpoint is queued
- **WHEN** a client posts an endpoint URL `http://example.org/sparql` with no graphs
- **THEN** the service answers `202` with a job id, and the job's state is `queued` or later

#### Scenario: An invalid URL is rejected
- **WHEN** a client posts the endpoint URL `ftp://example.org/sparql`
- **THEN** the service answers `400` with a problem response and queues no job

#### Scenario: An endpoint URL with user info is rejected
- **WHEN** a client posts the endpoint URL `https://user:secret@example.org/sparql`
- **THEN** the service answers `400` with a problem response and queues no job

### Requirement: Start a job for an uploaded RDF file
The service SHALL accept an uploaded RDF file in one of the serialisations supported today (`.ttl`
Turtle, `.rdf` RDF/XML, `.trix` TriX, `.nt` N-Triples, `.nq` N-Quads, `.n3` N3, `.jsonld` JSON-LD) and SHALL answer with the id of a queued job. It
SHALL reject any other file with a `415` problem response, and a file larger than the upload limit
(`RDF_FINGERPRINTER_MAX_UPLOAD_MB`, default 512) with a `413` problem response, keeping nothing of
it, before any job is queued (design R2-2).

#### Scenario: An RDF/XML file is queued
- **WHEN** a client uploads `continents-source-ap.rdf`
- **THEN** the service answers `202` with a job id

#### Scenario: An unsupported file is rejected
- **WHEN** a client uploads `notes.txt`
- **THEN** the service answers `415` with a problem response listing the accepted types, and queues no job

#### Scenario: A file over the upload limit is rejected
- **GIVEN** an upload limit of 1 MB
- **WHEN** a client uploads a 2 MB `.ttl` file
- **THEN** the service answers `413` with a problem response, keeps no part of the file and queues no job

### Requirement: An unavailable queue refuses the job
When the job queue (the Celery broker) cannot take a job, the service SHALL answer `503` with a
problem response and record the job `failed` with the reason, discarding a file job's upload; any
other error while queueing SHALL NOT be reported as an unavailable queue (design R2-4).

#### Scenario: The broker is down
- **GIVEN** the broker is not reachable
- **WHEN** a client posts an endpoint URL
- **THEN** the service answers `503` with a problem response and the job's record is `failed`

### Requirement: A job writes every output
A job that completes SHALL write, through the `rdf-fingerprinter` library, the report page
(`main.html`), the profile (`profile.json`), and the `shacl`, `puml`, `pattern`, `shex` and
`pitfalls` representations, with the pitfall scan on (DEC-1, DEC-2). When no graph was given, the
job SHALL profile the default graph and every named graph (DEC-3). The job SHALL NOT look up
prefixes on the network (DEC-15).

#### Scenario: An endpoint job writes all formats
- **GIVEN** a SPARQL endpoint holding the `continents-source-ap.rdf` fixture in its default graph
- **WHEN** a job fingerprints it and completes
- **THEN** its report holds the `html`, `json`, `shacl`, `puml`, `pattern`, `shex` and `pitfalls` outputs, each with at least one file

#### Scenario: The pitfall findings reach the report page
- **GIVEN** an endpoint whose data triggers at least one packaged pitfall check
- **WHEN** a job fingerprints it
- **THEN** `main.html` shows the findings and the `pitfalls` output holds them

#### Scenario: Named graphs are profiled when none is selected
- **GIVEN** an endpoint with data in the default graph and in the named graph `http://example.org/g1`
- **WHEN** a job fingerprints it with no graph selected
- **THEN** the profile covers both the default graph and `http://example.org/g1`

### Requirement: A file job cleans up after itself
A file job SHALL load the uploaded file into a temporary Fuseki dataset of its own, fingerprint that
dataset, and SHALL delete the dataset and the uploaded file when the job ends, whether it completed
or failed.

#### Scenario: The dataset is removed after success
- **WHEN** a file job completes
- **THEN** its temporary dataset no longer exists in Fuseki and its upload folder is removed

#### Scenario: The dataset is removed after failure
- **GIVEN** the library raises an error while fingerprinting the temporary dataset
- **WHEN** the file job fails
- **THEN** its temporary dataset no longer exists in Fuseki and its upload folder is removed

### Requirement: A job reports its state and failures
The service SHALL record each job from the moment it is accepted, and SHALL report its state as
exactly one of: `queued` (accepted, not started), `running` (started), `completed` (outputs saved,
no failure), `completed_with_failures` (outputs saved while some measurements failed; each failure
listed), `failed` (ended by an error; its reason given; no outputs kept) or `cancelled` (ended by a
client; no outputs kept) (DEC-11). An id the service never accepted SHALL answer `404`.

#### Scenario: A just-accepted job is queued
- **WHEN** a client asks for the state of a job right after it was accepted, before a worker takes it
- **THEN** the service answers `200` with state `queued`

#### Scenario: An unknown job is not found
- **WHEN** a client asks for the state of job `00000000-0000-0000-0000-000000000000`
- **THEN** the service answers `404` with a problem response

#### Scenario: An unreachable endpoint fails the job
- **WHEN** a job fingerprints `http://unreachable.invalid/sparql`
- **THEN** the job's state becomes `failed` and its reason names the unreachable endpoint

#### Scenario: Failed measurements are listed
- **GIVEN** an endpoint on which some measurements fail but the report is written
- **WHEN** the job ends
- **THEN** its state is `completed_with_failures` and its failures are listed in the job state and the report's metadata

#### Scenario: A running job can be cancelled
- **WHEN** a client cancels a running job
- **THEN** its state becomes `cancelled`, no outputs are kept, and a file job's temporary dataset is removed

#### Scenario: A finished job cannot be cancelled
- **GIVEN** a job in state `completed`
- **WHEN** a client cancels it
- **THEN** the service answers `409` and the job stays `completed`
