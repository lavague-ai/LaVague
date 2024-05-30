Feature: Swag Labs Login

  Scenario: Locked out user login attempt
    Given I am on the Swag Labs login page
    When I enter "locked_out_user" into the username field
    And I enter "secret_sauce" into the password field
    And I click the "Login" button
    Then I should see an error message saying "Sorry, this user has been locked out."