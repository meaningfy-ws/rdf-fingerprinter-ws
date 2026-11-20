# Spec: openspec/changes/upgrade-fingerprinter-library/specs/fingerprinting-jobs/spec.md
# One scenario per spec scenario, same name. Untagged scenarios run in the feature tier (fakes);
# @integration and @e2e scenarios are proven against containers (tasks.md, Test map) and are listed
# here so the whole behaviour reads in one place.
Feature: Fingerprinting jobs
  A client starts a job that fingerprints a SPARQL endpoint or an uploaded RDF file, follows its
  state, and gets every output the rdf-fingerprinter library offers.

  Rule: A job is started for a valid endpoint or a supported file, and nothing else

    Scenario: A valid endpoint is queued
      When a client posts the endpoint URL "http://example.org/sparql" with no graphs
      Then the service answers 202 with a job id
      And the job's state is "queued"

    Scenario: An invalid URL is rejected
      When a client posts the endpoint URL "ftp://example.org/sparql" with no graphs
      Then the service answers 400 with a problem response
      And no job is queued

    Scenario: An RDF/XML file is queued
      When a client uploads the file "continents-source-ap.rdf"
      Then the service answers 202 with a job id
      And the job's state is "queued"

    Scenario: An unsupported file is rejected
      When a client uploads the file "notes.txt"
      Then the service answers 415 with a problem response listing the accepted types
      And no job is queued

  Rule: A job writes every output the library offers

    @integration @e2e
    Scenario: An endpoint job writes all formats
      Given a SPARQL endpoint holding "continents-source-ap.rdf" in its default graph
      When a job fingerprints it and completes
      Then its report holds the html, json, shacl, puml, pattern, shex and pitfalls outputs, each with at least one file

    @integration
    Scenario: The pitfall findings reach the report page
      Given an endpoint holding "pitfall-untyped-class.ttl" in its default graph
      When a job fingerprints it
      Then the report page shows the pitfall findings
      And the pitfalls output holds them

    @integration
    Scenario: Named graphs are profiled when none is selected
      Given an endpoint with "continents-source-ap.rdf" in its default graph and "courts-source-ap.rdf" in the named graph "http://example.org/g1"
      When a job fingerprints it with no graph selected
      Then the profile covers the default graph and "http://example.org/g1"

  Rule: A file job removes its temporary dataset and upload, whatever the outcome

    Scenario: The dataset is removed after success
      Given a file job for "treaties-source-ap.rdf"
      When the job completes
      Then its temporary dataset is deleted
      And its upload folder is removed

    Scenario: The dataset is removed after failure
      Given a file job for "treaties-source-ap.rdf"
      And the library raises an error while fingerprinting
      When the job fails
      Then its temporary dataset is deleted
      And its upload folder is removed

  Rule: A job is in exactly one state, and failures are visible

    Scenario: A just-accepted job is queued
      Given an endpoint job was accepted and no worker has taken it
      When a client asks for its state
      Then the service answers 200 with state "queued"

    Scenario: An unknown job is not found
      When a client asks for the state of job "00000000-0000-0000-0000-000000000000"
      Then the service answers 404 with a problem response

    @e2e
    Scenario: An unreachable endpoint fails the job
      When a job fingerprints "http://unreachable.invalid/sparql"
      Then the job's state becomes "failed"
      And its reason names the unreachable endpoint

    Scenario: Failed measurements are listed
      Given an endpoint on which two measurements fail but the report is written
      When the job ends
      Then its state is "completed_with_failures"
      And both failures are listed in the job state and the report's metadata

    Scenario: A running job can be cancelled
      Given a file job that is queued
      When a client cancels it
      Then its state becomes "cancelled"
      And its upload is discarded and no outputs are kept

    Scenario: A finished job cannot be cancelled
      Given a job in state "completed"
      When a client cancels it
      Then the service answers 409
      And the job stays "completed"
