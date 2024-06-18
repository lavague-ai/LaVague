Feature: Cart

  Scenario: Add an item to cart
    Given the user is on the home page
    When the user clicks on a product
    And the user is on the product details page
    And the user clicks on 'ADD TO CART'
    And the user clicks on the Cart icon
    Then the user should see the item in the cart

