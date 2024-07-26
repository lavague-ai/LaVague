Feature: Add and remove a single product from cart

  Scenario: Add a product to cart
    Given I am on the homepage
    When I click "Accepter" to accept cookies
    And I enter "Harry Potter et la Chambre des Secrets" into the search bar and press Enter
    And I click on "Harry Potter et la Chambre des Secrets" in the search results
    And I am on the product details page
    And I click on the "Ajouter au panier" button
    And I am taken to a confirmation page
    And I click on "Aller au panier"
    And I am taken to the cart page
    And I remove the product from the cart by clicking on "Supprimer"
    Then the cart should be empty
