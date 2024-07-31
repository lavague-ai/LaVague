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
