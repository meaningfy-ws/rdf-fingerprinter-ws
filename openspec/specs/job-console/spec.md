# job-console Specification

## Purpose
The UI's console: list jobs with their live state and filters, start endpoint and file jobs (with the named-graph picker), cancel and delete with confirmation, safe from other sites. From `modernise-user-interface` (archived 2026-11-08).
## Requirements
### Requirement: One console lists every job with its state
The UI SHALL show one console page listing every job the API returns, newest first, with its
source (endpoint URL or file name), creation time and status, each status shown by its label
(`queued` Queued, `running` Running…, `completed` Done, `completed_with_failures` Done with warnings,
`failed` Failed, `cancelled` Cancelled) and not by colour
alone (DEC-4, DEC-8).

#### Scenario: Jobs in every state are listed
- **GIVEN** the API holds a completed job, a failed job and a running job
- **WHEN** a user opens the console
- **THEN** the page lists the three jobs, newest first, each with its source and its status label

#### Scenario: An empty console says so
- **GIVEN** the API holds no job
- **WHEN** a user opens the console
- **THEN** the page says there are no jobs and links to the two forms

### Requirement: The console filters jobs by state
The console SHALL offer the filters All, In progress (`queued`, `running`), Finished (`completed`,
`completed_with_failures`) and Failed or cancelled, as links that mark the current one; a filter
without jobs SHALL say so and offer All; a job the filter hides SHALL NOT be polled (U-3).

#### Scenario: A filter lists its states
- **GIVEN** the API holds a running, a completed and a cancelled job
- **WHEN** a user chooses "In progress"
- **THEN** only the running job is listed

### Requirement: Job state updates without reloading
While a job is `queued` or `running`, its row SHALL re-fetch its state from the UI at a fixed
interval and SHALL stop once the job reaches a final state; a state change SHALL be announced to
assistive technology without moving focus (DEC-3).

#### Scenario: A running job reaches completion
- **GIVEN** the console shows a job in state `running`
- **WHEN** the job completes
- **THEN** within one polling interval its row shows "Done" and its link to the report, the change
  is announced once, and polling stops

#### Scenario: Finished jobs do not poll
- **GIVEN** the console shows only jobs in final states
- **WHEN** the page is open
- **THEN** no state request is sent

#### Scenario: Updates pause while the service is down
- **GIVEN** the console shows a running job
- **WHEN** the API gives no answer to a poll
- **THEN** the page says status updates are paused and keeps polling

### Requirement: Start a job from an endpoint or a file
The UI SHALL offer a form for a SPARQL endpoint URL with optional named graphs and a form for an
uploaded file of a supported type, naming the accepted types and the upload limit; on success it
SHALL show the new job in the console in state `queued`; on an API error it SHALL keep the user's
input and show a plain sentence for the error next to the field it concerns (design, Error matrix).
A file well beyond the limit SHALL be refused by the UI without being sent to the API.

#### Scenario: An endpoint job is started
- **WHEN** a user submits `http://example.org/sparql` with no graph chosen
- **THEN** the console shows a new job for that URL with status "Queued" (or later)

#### Scenario: An invalid URL is refused
- **WHEN** a user submits `not a url`
- **THEN** the form is shown again with the URL kept and a message naming the field

#### Scenario: An unsupported file is refused
- **WHEN** a user uploads `notes.docx`
- **THEN** the form is shown again with the sentence naming the accepted file types

#### Scenario: A file over the limit is refused
- **WHEN** a user uploads a file larger than the upload limit
- **THEN** the form is shown again with the sentence naming the limit

### Requirement: Choose named graphs from the endpoint
The endpoint form SHALL offer the endpoint's named graphs, listed through the API (the library's
`list_named_graphs`, rdf-fingerprinter 3.6.0), as choices; no
choice SHALL mean all graphs. When the listing fails the form SHALL say why and still accept a
submission without graphs (DEC-9). A submission with graphs listed for another endpoint URL than the
one in the form SHALL be refused.

#### Scenario: Two graphs are chosen
- **GIVEN** an endpoint with the named graphs `http://ex.org/g1`, `http://ex.org/g2` and
  `http://ex.org/g3`
- **WHEN** a user enters its URL, asks for its graphs and chooses `g1` and `g3`
- **THEN** the job is started with exactly those two graphs

#### Scenario: The endpoint cannot be reached for its graphs
- **WHEN** a user asks for the graphs of an unreachable endpoint
- **THEN** the form says the endpoint could not be reached and offers no graph choices

#### Scenario: Graphs belong to another endpoint
- **GIVEN** graphs listed for `http://e/sparql` and chosen
- **WHEN** the user changes the URL to `http://other/sparql` and starts the job
- **THEN** no job is started, and the form says the graphs belong to another endpoint and to load them again

### Requirement: Cancel and delete ask first
Cancelling a `queued` or `running` job and deleting a report SHALL be `POST` actions behind a
confirmation that names the job; the outcome SHALL be shown as a message (DEC-8). Only a job in a final
state SHALL offer delete; an active one offers cancel.

#### Scenario: A running job is cancelled
- **GIVEN** a running job
- **WHEN** a user chooses cancel and confirms
- **THEN** the job shows status "Cancelled"

#### Scenario: A delete is abandoned
- **WHEN** a user chooses delete on a report and then declines the confirmation
- **THEN** the report is still listed

#### Scenario: A finished job offers no cancel
- **GIVEN** a completed job
- **WHEN** a user views it
- **THEN** no cancel action is offered

### Requirement: Forms and pages are safe from other sites
Every form that changes state SHALL carry a CSRF token; a `POST` without a valid token SHALL be
refused, and an expired token SHALL show the form again, with what was typed, and the sentence
"This form expired. Please try again.". Every UI response SHALL refuse framing by another site
(`X-Frame-Options: SAMEORIGIN`, `frame-ancestors 'self'`). A return address (`next`) SHALL be
followed only when it is a local path; anything else SHALL land on the console. The session cookie
SHALL be `SameSite=Lax`, and `Secure` when `RDF_FINGERPRINTER_UI_SECURE_COOKIES` is true (design
S1-1, S1-2).

#### Scenario: A delete without the token is refused
- **WHEN** a client posts a delete without the CSRF token
- **THEN** the UI refuses it and the report is still listed

#### Scenario: A return address to another site is ignored
- **WHEN** a user confirms a cancel with `next=//evil.example/`
- **THEN** the UI lands on the console

#### Scenario: Pages are not framed by other sites
- **WHEN** any UI page is loaded
- **THEN** its response carries `X-Frame-Options: SAMEORIGIN` and `frame-ancestors 'self'`

