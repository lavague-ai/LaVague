Scenario: Submission with missing phone number
      Given I am on the job application page
      When I enter "John" in the "First Name" field
      And I enter "Doe" in the "Last Name" field
      And I enter "john.doe@example.com" in the "Email Address" field
      And I leave the "Phone Number" field empty
      And I enter "I am very interested in this position." in the "Cover Letter" field
      And I click the "Apply" button
      Then I should see an error message for the "Phone Number" field