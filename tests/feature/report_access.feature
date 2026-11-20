# Spec: openspec/changes/upgrade-fingerprinter-library/specs/report-access/spec.md
# One scenario per spec scenario, same name. Untagged scenarios run in the feature tier (fakes);
# @unit scenarios are proven by unit tests (tasks.md, Test map).
Feature: Report access
  A client lists reports, downloads a report's outputs one format at a time or as one zip, and
  deletes reports.

  Rule: Every job is listed with its state

    Scenario: A completed job appears in the list
      Given a job that completed for "http://example.org/sparql"
      When a client lists the reports
      Then the list holds that report with its source, state "completed" and its seven formats

    Scenario: A failed job appears without formats
      Given a job that failed because "http://unreachable.invalid/sparql" was unreachable
      When a client lists the reports
      Then the list holds that job with state "failed", its reason, and no formats

  Rule: Outputs are downloaded by format name

    Scenario: The report page is downloaded
      Given a completed report
      When a client downloads its format "html"
      Then it receives "main.html" as "text/html"

    @unit
    Scenario: A multi-file format is zipped
      Given a completed report with two PlantUML files
      When a client downloads its format "puml"
      Then it receives a zip holding those two files and nothing else

    @unit
    Scenario: Everything is zipped
      Given a completed report
      When a client downloads its format "zip"
      Then it receives a zip holding the files of every format

    Scenario: An unknown format is rejected
      Given a completed report
      When a client downloads its format "pdf"
      Then the service answers 400 with a problem response

    Scenario: An unknown report is not found
      When a client downloads format "html" of a report id the service never issued
      Then the service answers 404 with a problem response

    Scenario: A format with no file is not found
      Given a completed report whose "shacl" output holds no file
      When a client downloads its format "shacl"
      Then the service answers 404 with a problem response

  Rule: Reports can be deleted, one or all

    Scenario: A report is deleted
      Given a completed report
      When a client deletes it
      Then it is no longer listed and its files are gone

    Scenario: All reports are deleted
      Given two completed reports
      When a client deletes all reports
      Then the service answers 200 and the list is empty

    Scenario: Deleting an unknown report
      When a client deletes a report id the service never issued
      Then the service answers 404 with a problem response

  Rule: The UI shows every format and the job's failures

    @unit
    Scenario: The report page lists the downloads
      Given a completed report
      When a user opens it in the UI
      Then the page shows a link for each format and for the zip

    @unit
    Scenario: Failures are shown
      Given a report whose job ended "completed_with_failures"
      When a user opens it in the UI
      Then the page shows the state and lists the failures
