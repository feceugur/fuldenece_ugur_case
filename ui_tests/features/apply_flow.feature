@apply
Feature: Apply Flow — From Job Listing to Application Form
  As a QA candidate
  I want to click Apply and reach the Lever application form
  So that I can submit my application

  Background:
    Given I am on the Lever QA jobs page

  @smoke
  Scenario: All Apply button URLs follow the Lever job URL pattern
    Then all Apply button hrefs should match the Lever job URL pattern

  @smoke
  Scenario: Clicking Apply navigates to a Lever job page
    When I click the Apply button on the first Istanbul posting
    Then I should be on a Lever job page for Insider One

  @smoke
  Scenario: Application form contains required fields
    When I navigate to the apply form of the first Istanbul posting
    Then the application form should have a name field
    And the application form should have an email field
    And the application form should have a resume upload field

  @regression
  Scenario: Apply page title is not empty
    When I navigate to the apply form of the first Istanbul posting
    Then the apply page title should not be empty

  @regression
  Scenario: Each Apply button links to a unique job
    Then all Apply button hrefs should be unique
