## ADDED Requirements

### Requirement: The worker renders the class diagram
After a job's outputs are written, the worker SHALL render the PlantUML file the library returns for `puml` to
SVG through the PlantUML server of the stack and store it as `puml/diagram.svg`, so it is part of
the `puml` download and the zip. The diagram SHALL be sent to no server outside the stack (DEC-6,
DEC-7).

#### Scenario: A diagram is rendered
- **GIVEN** an endpoint job whose library run returned a PlantUML file
- **WHEN** the job's outputs are saved
- **THEN** the report holds `puml/diagram.svg`, a valid SVG, and the job is `completed`

### Requirement: A rendering failure does not fail the job
A job SHALL end `completed_with_failures`, with a failure naming the diagram rendering and its
cause, when the PlantUML server is unreachable, refuses the diagram or exceeds its size limit; every
other output SHALL be kept.

#### Scenario: The PlantUML server is down
- **GIVEN** the PlantUML server is not reachable
- **WHEN** a job's outputs are saved
- **THEN** the job is `completed_with_failures`, its failures name the diagram rendering, and its
  other seven formats are downloadable

### Requirement: Download the diagram as SVG
The API SHALL serve `puml/diagram.svg` as format `svg` (`image/svg+xml`); a job without it SHALL
answer `404`.

#### Scenario: The SVG is downloaded
- **WHEN** a client downloads format `svg` of a job holding a rendered diagram
- **THEN** it receives that SVG as `image/svg+xml`
