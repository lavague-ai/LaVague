Feature: Wikipedia Login

  Scenario: User logs in successfully
    Given the user is on the Wikipedia homepage
    When the user navigates to the login page
    And the user enters Lavague-test in the username field
    And the user enters lavaguetest123 in the password field
    And the user clicks on the login button under the username and password fields
    And the user clicks on Lavague-test
    Then the user should be logged in on the profile page
