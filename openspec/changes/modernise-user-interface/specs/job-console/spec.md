## ADDED Requirements

### Requirement: One console lists every job with its state
The UI SHALL show one console page listing every job the API returns, newest first, with its
source (endpoint URL or file name), creation time and state (`queued`, `running`, `completed`,
`completed_with_failures`, `failed`, `cancelled`), each state shown by text and not by colour
alone (DEC-4, DEC-8).

#### Scenario: Jobs in every state are listed
- **GIVEN** the API holds a completed job, a failed job and a running job
- **WHEN** a user opens the console
- **THEN** the page lists the three jobs, newest first, each with its source and its state as text

#### Scenario: An empty console says so
- **GIVEN** the API holds no job
- **WHEN** a user opens the console
- **THEN** the page says there are no jobs and links to the two forms

### Requirement: Job state updates without reloading
While a job is `queued` or `running`, its row SHALL re-fetch its state from the UI at a fixed
interval and SHALL stop once the job reaches a final state; a state change SHALL be announced to
assistive technology without moving focus (DEC-3).

#### Scenario: A running job reaches completion
- **GIVEN** the console shows a job in state `running`
- **WHEN** the job completes
- **THEN** within one polling interval its row shows `completed` and its link to the job page, and
  the row stops polling

#### Scenario: Finished jobs do not poll
- **GIVEN** the console shows only jobs in final states
- **WHEN** the page is open
- **THEN** no state request is sent

### Requirement: Start a job from an endpoint or a file
The UI SHALL offer a form for a SPARQL endpoint URL with optional named graphs and a form for an
uploaded file of a supported type; on success it SHALL show the new job in the console in state
`queued`; on an API error it SHALL keep the user's input and show the API's message next to the
form.

#### Scenario: An endpoint job is started
- **WHEN** a user submits `http://example.org/sparql` with no graph chosen
- **THEN** the console shows a new job for that URL in state `queued`

#### Scenario: An invalid URL is refused
- **WHEN** a user submits `not a url`
- **THEN** the form is shown again with the URL kept and a message naming the field

#### Scenario: An unsupported file is refused
- **WHEN** a user uploads `notes.docx`
- **THEN** the form is shown again with the API's message about the file type

### Requirement: Choose named graphs from the endpoint
The endpoint form SHALL offer, once the library's public graph listing is released
(`meaningfy-ws/rdf-fingerprinter#63`), the endpoint's named graphs, listed through the API, as choices; no
choice SHALL mean all graphs. When the listing fails the form SHALL say why and still accept a
submission without graphs (DEC-9).

#### Scenario: Two graphs are chosen
- **GIVEN** an endpoint with the named graphs `http://ex.org/g1`, `http://ex.org/g2` and
  `http://ex.org/g3`
- **WHEN** a user enters its URL, asks for its graphs and chooses `g1` and `g3`
- **THEN** the job is started with exactly those two graphs

#### Scenario: The endpoint cannot be reached for its graphs
- **WHEN** a user asks for the graphs of an unreachable endpoint
- **THEN** the form says the endpoint could not be reached and offers no graph choices

### Requirement: Cancel and delete ask first
Cancelling a `queued` or `running` job and deleting a report SHALL be `POST` actions behind a
confirmation that names the job; the outcome SHALL be shown as a message (DEC-8).

#### Scenario: A running job is cancelled
- **GIVEN** a running job
- **WHEN** a user chooses cancel and confirms
- **THEN** the job shows state `cancelled`

#### Scenario: A delete is abandoned
- **WHEN** a user chooses delete on a report and then declines the confirmation
- **THEN** the report is still listed

#### Scenario: A finished job offers no cancel
- **GIVEN** a completed job
- **WHEN** a user views it
- **THEN** no cancel action is offered
