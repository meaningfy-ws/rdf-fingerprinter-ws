## ADDED Requirements

### Requirement: List reports
The service SHALL list every job record, whatever its state, with its id, its source (the endpoint
URL or the file name), the graphs requested, its creation time, the time it reached a final state
(`finished_at`), its state, its reason, its failures, the formats it holds and the files of each
format (`files`; added by `modernise-user-interface` U-7). A record written before `finished_at`
and `files` existed SHALL still be listed, its files read from its format folders.

#### Scenario: A completed job appears in the list
- **GIVEN** a job that completed for `http://example.org/sparql`
- **WHEN** a client lists the reports
- **THEN** the list holds that report with its source, `completed` state and its seven formats

#### Scenario: A failed job appears without formats
- **GIVEN** a job that failed because its endpoint was unreachable
- **WHEN** a client lists the reports
- **THEN** the list holds that job with state `failed`, its reason, and no formats

#### Scenario: A finished job carries its end time and files
- **GIVEN** a job that completed
- **WHEN** a client reads its record
- **THEN** the record holds `finished_at` and, per format, the names of its files

### Requirement: Download a report by format
The service SHALL let a client download a report's output by format name: `html` (the report page),
`json` (the profile), `shacl`, `puml`, `pattern`, `shex`, `pitfalls`, or `zip` (every output). An
output of one file SHALL be returned as that file; an output of several files SHALL be returned as
a zip of that format's files (DEC-5). An unknown format SHALL answer `400`; an unknown report, or a
format with no file in that report, SHALL answer `404`.

#### Scenario: The report page is downloaded
- **WHEN** a client downloads format `html` of a completed report
- **THEN** it receives `main.html` as `text/html`

#### Scenario: A multi-file format is zipped
- **WHEN** a client downloads format `puml` of a completed report
- **THEN** it receives a zip holding that report's PlantUML files and nothing else

#### Scenario: Everything is zipped
- **WHEN** a client downloads format `zip`
- **THEN** it receives a zip holding the files of all seven formats

#### Scenario: An unknown format is rejected
- **WHEN** a client downloads format `pdf`
- **THEN** the service answers `400` with a problem response

#### Scenario: An unknown report is not found
- **WHEN** a client downloads format `html` of a report id the service never issued
- **THEN** the service answers `404` with a problem response

#### Scenario: A format with no file is not found
- **GIVEN** a report whose `shacl` output holds no file
- **WHEN** a client downloads format `shacl`
- **THEN** the service answers `404` with a problem response

### Requirement: Delete reports
The service SHALL delete one report by id, and SHALL delete all reports on request (answering
`200` even when there were none). Deleting an unknown report SHALL answer `404`; deleting a job
that is `queued` or `running` SHALL answer `409` and leave the job as it is (added by
`modernise-user-interface` U-3: cancel first).

#### Scenario: A report is deleted
- **WHEN** a client deletes a report by its id
- **THEN** the report is no longer listed and its files are gone

#### Scenario: All reports are deleted
- **GIVEN** two reports
- **WHEN** a client deletes all reports
- **THEN** the service answers `200` and the list is empty

#### Scenario: Deleting an unknown report
- **WHEN** a client deletes a report id the service never issued
- **THEN** the service answers `404` with a problem response

#### Scenario: An active job cannot be deleted
- **GIVEN** a running job
- **WHEN** a client deletes it
- **THEN** the service answers `409` with a problem response and the job is still running

### Requirement: The UI offers every format
The web UI SHALL show, for each report, a download link per format the report holds and the job's
state, with its failures when there are any (DEC-10).

#### Scenario: The report page lists the downloads
- **GIVEN** a completed report
- **WHEN** a user opens it in the UI
- **THEN** the page shows a link for each of the seven formats and for the zip

#### Scenario: Failures are shown
- **GIVEN** a report whose job ended `completed_with_failures`
- **WHEN** a user opens it in the UI
- **THEN** the page shows the state and lists the failures
