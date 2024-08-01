Feature: Shipping cost calculator

  Scenario: Estimate shipping costs for a large package
    Given the user is on the homepage
    When the user clicks on "J'accepte" to accept cookies
    And the user clicks on "Envoyer un colis"
    And the user clicks on the "Format du colis" dropdown under "Dimension"
    And the user clicks on "Volumineux & tube" from the dropdown results
    And the user enters 15 in the "Poids" field
    And the user waist for the cost to update
    Then the cost should be "34,70 €"
