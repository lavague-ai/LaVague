Feature: Login

  Scenario: Successful login with valid credentials
    Given the user is on the Swag Labs login page
    When the user enters "standard_user" as the username
    And the user enters "secret_sauce" as the password
    And the user clicks the login button
    Then the user should be redirected to the home page
    And the user should see the product inventory

  Scenario: Attempt to login with invalid credentials
    Given the user is on the Swag Labs login page
    When the user enters "invalid_user" as the username
    And the user enters "wrong_password" as the password
    And the user clicks the login button
    Then the user should see an error message
    And the error message should say "Username and password do not match any user in this service."