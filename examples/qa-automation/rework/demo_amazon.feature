Feature: Amazon Cart

  Scenario: Add and remove a single product from cart
    Given I am on the homepage
    When I click "Accepter" to accept cookies
    And I enter "Harry Potter et la Chambre des Secrets poche" into the search bar and press Enter
    And I click on the first book in the search results
    And I click on the "Ajouter au panier" button
    And I click on "Aller au panier" under "Passer la commande"
    And I click on "Supprimer" from the cart page
    Then the cart should be empty
