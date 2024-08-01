# LaVague QA Examples

We will periodically add [examples in our repository](https://github.com/lavague-ai/LaVague/blob/main/lavague/features/). In this section, we will go over each of the Gherkin files and showcase the generated code. 


| URL                              | Link to file                                                  | Purpose                                                  |
|:---------------------------------|:--------------------------------------------------------------|:---------------------------------------------------------|
| https://amazon.fr/               | [demo_amazon.feature](https://github.com/lavague-ai/LaVague/blob/main/lavague/features/demo_amazon.feature)       | Tests the Amazon search, cart and cart deletion to ensure expected behavior |
| https://laposte.fr/              | [demo_laposte.feature](https://github.com/lavague-ai/LaVague/blob/main/lavague/features/demo_laposte.feature)     | Tests an interative shipping cost calculator to ensure expected output |
| https://en.wikipedia.org/        | [demo_wikipedia.feature](https://github.com/lavague-ai/LaVague/blob/main/lavague/features/demo_wikipedia.feature) | Tests the login feature of Wikipedia  |
| https://hsbc.fr/                 | [demo_hsbc.feature](https://github.com/lavague-ai/LaVague/blob/main/lavague/features/demo_hsbc.feature)           | Tests proper multitab navigation and cookie banners |


In each of these examples, we'll showcase how LaVague QA can be used to generate tests for critical parts of your websites. 

## Amazon Cart testing

The cart is a core feature in e-commerce and companies need to ensure it always stays functionnal. 

### Feature file

```gherkin
Feature: Cart

  Scenario: Add and remove a single product from cart
    Given the user is on the homepage
    When the user clicks on "Accepter" to accept cookies
    And the user enter "Zero to One" into the search bar and press Enter
    And the user click on the first product in the search results
    And the user click on the "Ajouter au panier" button
    And the user the confirmation message has been displayed
    And the user click on "Aller au panier" under "Passer la commande"
    And the user click on "Supprimer" from the cart page
    Then the cart should be empty
```

## Interactive shipping calculator testing

Interactive components need to be tested to ensure they maintain valid output over time.

### Feature file

```gherkin
Feature: Cart

  Scenario: Add and remove a single product from cart
    Given the user is on the homepage
    When the user clicks on "Accepter" to accept cookies
    And the user enter "Zero to One" into the search bar and press Enter
    And the user click on the first product in the search results
    And the user click on the "Ajouter au panier" button
    And the user the confirmation message has been displayed
    And the user click on "Aller au panier" under "Passer la commande"
    And the user click on "Supprimer" from the cart page
    Then the cart should be empty
```

## Wikipedia login testing


### Feature file

Login is a core part of most websites, we test basic login functionnality by providing credentials. 

```gherkin
Feature: Wikipedia Login

  Scenario: User logs in successfully
    Given the user is on the Wikipedia homepage
    When the user navigates to the login page
    And the user enters Lavague-test in the username field
    And the user enters lavaguetest123 in the password field
    And the user clicks on login under the username and password field
    Then the login is successful and the user is redirected to the main page
```

## Test cookies and redirections work as expected

Certain websites have several cookie banners and redirect users often, use LaVague QA to validate linking on your sites. 

### Feature file

```gherkin
Feature: HSBC navigation

  Scenario: Multi tab navigation
    Given the user is on the HSBC homepage
    When the user clicks on "Tout accepter" to accept cookies
    And the user clicks on "Global Banking and Markets"
    And the user clicks on "Je comprends, continuons"
    And the user navigates to the new tab opened
    And the user clicks on "Accept all cookies"
    And the user clicks on "About us"
    Then the user should be on the "About us" page of the "Global Banking and Markets" services of HSBC

```




