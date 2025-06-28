Feature: Login functionality
  @positive
  Scenario: Successful login
    Given the user opens the login page
    When the user clicks on Make Appointment
    When the user enters username "John Doe"
    And the user enters password "ThisIsNotAPassword"
    And the user clicks login
    Then the user should see the dashboard
