## ADDED Requirements

### Requirement: A job page shows the report
For a job in state `completed` or `completed_with_failures`, the job page SHALL show the library's
report page (`html`) inside a frame sandboxed with scripts allowed and without same-origin access,
with a link that opens it in a new tab; the UI SHALL NOT alter the report's content (DEC-5).

#### Scenario: The report is read in the page
- **GIVEN** a completed endpoint job
- **WHEN** a user opens its job page
- **THEN** the page holds a frame whose `sandbox` is `allow-scripts` and whose content is that
  job's `main.html`, including its pitfall section

### Requirement: A job page shows the class diagram
When the job holds `puml/diagram.svg`, the job page SHALL show it as an image with a text
alternative; when it does not, the page SHALL say that no diagram is available and why, taken from
the job's failures.

#### Scenario: The diagram is shown
- **GIVEN** a completed job whose diagram was rendered
- **WHEN** a user opens its job page
- **THEN** the page shows the diagram image with a text alternative naming the job's source

#### Scenario: The diagram failed to render
- **GIVEN** a job in state `completed_with_failures` whose failures include the diagram rendering
- **WHEN** a user opens its job page
- **THEN** the page says no diagram is available and shows that failure

### Requirement: A job page offers every download
The job page SHALL list each format the job holds with a download link, and the zip of all
outputs.

#### Scenario: Downloads are listed
- **GIVEN** a completed job
- **WHEN** a user opens its job page
- **THEN** the page links to `html`, `json`, `shacl`, `puml`, `svg`, `pattern`, `shex`, `pitfalls`
  and `zip`

### Requirement: Failures and reasons are visible
The job page SHALL list a `completed_with_failures` job's failures and show a `failed` job's
reason; a `failed` or `cancelled` job SHALL offer no report, diagram or downloads.

#### Scenario: An unreachable endpoint
- **GIVEN** a job that failed because its endpoint was unreachable
- **WHEN** a user opens its job page
- **THEN** the page shows state `failed` and the reason, and no report frame

### Requirement: The UI is accessible and self-contained
Every page SHALL pass an axe-core WCAG 2.2 AA check in the light and dark themes, be usable by
keyboard alone and at 360 px wide, and load no script, style or font from outside the UI (DEC-1,
DEC-8).

#### Scenario: No external assets
- **WHEN** any UI page is loaded
- **THEN** every script, stylesheet and font it requests is served by the UI itself

#### Scenario: Both themes pass
- **WHEN** the console and a job page are checked with axe-core in the light and in the dark theme
- **THEN** no WCAG 2.2 AA violation is reported
