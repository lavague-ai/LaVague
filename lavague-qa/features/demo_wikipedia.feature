Feature: Wikipedia Login

  Scenario: User logs in successfully
    Given the user is on the Wikipedia homepage
    When the user navigates to the login page
    And the user enters Lavague-test in the username field
    And the user enters lavaguetest123 in the password field
    And the user clicks on login under the username and password field
    Then the login is successful and the user is redirected to the main page
