Feature: Cart

  Scenario: Add and remove a single product from cart
    Given the user is on the homepage
    When the user clicks on "Accepter" to accept cookies
    And the user enters "Zero to One" into the search bar and press Enter
    And the user clicks on the first product in the search results
    And the user clicks on the "Ajouter au panier" button
    And the confirmation message is displayed
    And the user clicks on "Aller au panier" under "Passer la commande"
    And the user clicks on "Supprimer" from the cart page
    Then the cart should be empty
