Feature: Shipping cost calculator

  Scenario: Estimate shipping costs for a large package
    Given I am on the homepage
    When I click on "J'accepte" to accept cookies
    And I click on "Envoyer un colis"
    And I click on the "Format du colis" dropdown under "Dimension"
    And I click on "Volumineux & tube" from the dropdown results
    And I enter 15 in the "Poids" field
    And I wait for the cost to update
    Then the cost should be "34,70 €"
