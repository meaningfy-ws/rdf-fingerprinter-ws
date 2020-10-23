# Date:  15/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

Feature: Fingerprint from UI
  The fingerprinting report to be returned after data upload.

  Scenario: Fingerprint SPARQL endpoint
    Given the SPARQL_ENDPOINT_URL with value http://fuseki:3030/test-dataset/query
    When I navigate to the location /fingerprint-sparql-endpoint
    And I fill in the field sparql_endpoint_url with SPARQL_ENDPOINT_URL
    And I click on the button with id submit
    # to be updated
    Then something happens


  Scenario Outline: Fingerprint an RDF file
    Given the <field> with value <value>
    When I navigate to the location /fingerprint-file
    And I upload in the field <field_id> with <field>
    And I click on the button with id submit
    # to be updated
    Then something happens

    Examples: Files with different sizes (small, medium, big)
      | field     | field_id  | value                               |
      | DATA_FILE | data_file | resources/continents-source-ap.rdf |
      | DATA_FILE | data_file | resources/treaties-source-ap.rdf   |
      | DATA_FILE | data_file | resources/courts-source-ap.rdf     |
