## ADDED Requirements

### Requirement: Every page ends with the footer
Every page of the UI SHALL end with one footer that shows the Meaningfy logo, linking to
`https://meaningfy.lu`, and under it the line "Made with love in Luxembourg", where "love" is shown
as a red heart hidden from assistive technology; the footer SHALL link to this repository
(`https://github.com/meaningfy-ws/rdf-fingerprinter-ws`) and name the licence, Apache-2.0, linking
to `LICENSE` on the repository's `main` branch; every link that leaves the UI SHALL carry
`rel="noopener"` (DEC-2, DEC-3, DEC-5, DEC-8). The footer SHALL show the version of the installed
package, read at start-up and never written in a template (DEC-6). The heart SHALL pulse through
CSS only and SHALL be still under `prefers-reduced-motion: reduce`; the footer SHALL need no
JavaScript (DEC-4).

#### Scenario: Every page ends with the footer
- **GIVEN** the API holds a completed job
- **WHEN** a user opens the jobs list, the new-job page, the job's report viewer or the page of a
  job that does not exist
- **THEN** the page ends with a footer that names Meaningfy, reads "Made with love in Luxembourg"
  and links to the Meaningfy website, the repository and the licence, each with `rel="noopener"`

#### Scenario: The footer shows the installed version
- **WHEN** a user opens the jobs list
- **THEN** the footer shows "v" followed by the version of the installed `rdf-fingerprinter-ws`
  package

#### Scenario: The heart is hidden from assistive technology
- **WHEN** a user opens the jobs list
- **THEN** the heart and the logo drawing are marked `aria-hidden`, and the footer's text still
  reads "Meaningfy" and "Made with love in Luxembourg"

#### Scenario: The pulse stops under reduced motion
- **WHEN** the stylesheet is read
- **THEN** the heart's animation is declared in CSS, and a `prefers-reduced-motion: reduce` rule
  switches animations off for it

#### Scenario: The image knows its version
- **WHEN** the UI image is built and asked for the version of `rdf-fingerprinter-ws`
- **THEN** it answers the version in `pyproject.toml`, and the UI's templates, stylesheet and the
  API's OpenAPI file are in the installed package
