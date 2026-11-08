## ADDED Requirements

### Requirement: The worker renders the class diagram
After a job's outputs are written, the worker SHALL render every PlantUML file the library wrote
for the job to SVG through the PlantUML server of the stack and store them as the format `svg`, one
SVG per PlantUML file with the same stem, so they are part of the zip. No diagram SHALL be sent to a
server outside the stack (DEC-6, DEC-7).

#### Scenario: A diagram is rendered
- **GIVEN** an endpoint job whose library run wrote a whole-model diagram and two vocabulary diagrams
- **WHEN** the job's outputs are saved
- **THEN** the job's `svg` format holds three valid SVGs named after them, and the job is `completed`

### Requirement: A rendering failure does not fail the job
A job SHALL end `completed_with_failures`, with a failure naming the diagram rendering and its
cause, when the PlantUML server is unreachable, times out or refuses the diagram; the diagrams that
were drawn and every other output SHALL be kept.

#### Scenario: The PlantUML server is down
- **GIVEN** the PlantUML server is not reachable
- **WHEN** a job's outputs are saved
- **THEN** the job is `completed_with_failures`, its failures name the diagram rendering, and its
  other seven formats are downloadable

### Requirement: Diagrams are served one by one
The API SHALL list a job's files per format in its record, SHALL serve one named file of a format
(`GET /reports/{uid}/{format}/{file}`), with `image/svg+xml` for an SVG, and SHALL serve format
`svg` whole like any other format; an unknown file SHALL answer `404`.

#### Scenario: One diagram is fetched
- **GIVEN** a job whose `svg` format holds `diagram-default.svg`
- **WHEN** a client fetches `/reports/{uid}/svg/diagram-default.svg`
- **THEN** it receives that SVG as `image/svg+xml`

#### Scenario: An unknown diagram is not found
- **WHEN** a client fetches `/reports/{uid}/svg/nothing.svg`
- **THEN** the service answers `404` with a problem response
