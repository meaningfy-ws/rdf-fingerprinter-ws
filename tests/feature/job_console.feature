# Spec: openspec/changes/improve-ui-footer/specs/job-console/spec.md
# One scenario per spec scenario, same name. Untagged scenarios run in the feature tier (the UI's
# test client over a fake API); @unit scenarios are proven by unit tests (tasks.md, Test map).
Feature: Job console footer
  Every page of the UI ends with one footer that credits Meaningfy and names the licence and version.

  Rule: Every page ends with the footer

    Scenario Outline: Every page ends with the footer
      Given the API holds a completed job
      When a user opens <page>
      Then the page ends with a footer that names Meaningfy and reads "Made with love in Luxembourg"
      And the footer links to the Meaningfy website, the repository and the licence, each with rel "noopener"

      Examples:
        | page                           |
        | the jobs list                  |
        | the new-job page               |
        | the job's report viewer        |
        | the page of a job that does not exist |

    Scenario: The footer shows the installed version
      Given the API holds a completed job
      When a user opens the jobs list
      Then the footer shows "v" followed by the version of the installed package

    Scenario: The heart is hidden from assistive technology
      Given the API holds a completed job
      When a user opens the jobs list
      Then the heart and the logo drawing are marked aria-hidden
      And the footer's text still reads "Meaningfy" and "Made with love in Luxembourg"

    @unit
    Scenario: The pulse stops under reduced motion
      When the stylesheet is read
      Then the heart's animation is declared in CSS, and a prefers-reduced-motion rule switches animations off for it

    @unit
    Scenario: The image knows its version
      When the UI image is built and asked for the version of rdf-fingerprinter-ws
      Then it answers the version in pyproject.toml, and the UI's templates, stylesheet and the API's OpenAPI file are in the installed package
