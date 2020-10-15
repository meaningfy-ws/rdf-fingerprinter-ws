# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

Feature: Fingerprint from UI
  The fingerprinting report to be returned after data upload.

  Scenario Outline: Fingerprint user provided data
    Given a <fingeprinting_type>
    When the user uploads the <data> and requests the fingerprinting report
    Then the file is uploaded and sent to the <api_endpoint> for fingerprinting
    And the report is received from the API call
    And the user gets the report

    Examples:
      | fingeprinting_type | data                            | api_endpoint                                      |
      | RDF file           | /tests/test_data/rdf-file.ttl   | http://localhost:4020/fingerprint-file            |
      | SPARQL endpoint    | http://localhost:3030/endpoint/ | http://localhost:4020/fingerprint-sparql-endpoint |
