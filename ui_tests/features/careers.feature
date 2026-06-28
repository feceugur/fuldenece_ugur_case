@careers
Feature: Insider One Careers Page — Team Navigation
  As a job seeker
  I want to browse open positions by department
  So that I can find and apply for QA roles

  Background:
    Given I am on the Insider One careers page

  @smoke
  Scenario: Careers page title contains "career"
    Then the careers page title should contain "career"

  @smoke
  Scenario: Open roles section is visible
    Then the open roles section should be visible

  @smoke
  Scenario: "See all teams" button is present
    Then the "See all teams" button should be visible

  @smoke
  Scenario: "See all teams" button uses a JS handler, not an external URL
    Then the "See all teams" button href should not be an external URL

  @smoke
  Scenario: Quality Assurance department card appears after clicking See all teams
    When I click "See all teams"
    Then the "Quality Assurance" department card should be visible

  @regression
  Scenario: QA card shows a positive open position count
    When I click "See all teams"
    Then the "Quality Assurance" card should show more than 0 open positions

  @regression
  Scenario: QA card button links to Lever with correct team filter
    When I click "See all teams"
    Then the "Quality Assurance" card button should link to Lever with team filter "Quality%20Assurance"

  @smoke
  Scenario: Clicking QA card navigates to Lever QA jobs page
    When I click "See all teams"
    And I click the "Quality Assurance" open positions button
    Then I should be on a Lever page filtered for "Quality" Assurance

  @regression
  Scenario: Cards with 0 positions do not use team-filtered Lever URLs
    When I click "See all teams"
    Then cards with 0 open positions should not have a team-filtered Lever URL
