@job_listings
Feature: QA Job Listings on Lever
  As a QA job seeker
  I want to see all Quality Assurance positions with accurate details
  So that I can find roles matching my location and department

  Background:
    Given I am on the Lever QA jobs page

  @smoke
  Scenario: QA jobs list is not empty
    Then there should be at least 1 job posting

  @smoke
  Scenario: Every posting has a non-empty title
    Then every posting should have a non-empty title

  @smoke
  Scenario: Every posting has an Apply button
    Then every posting should have an Apply button

  @smoke
  Scenario: Every posting has a location
    Then every posting should have a location

  @bug
  Scenario: All position titles contain "Quality Assurance"
    Then all position titles should contain "Quality Assurance"

  @regression
  Scenario: No position title is blank
    Then no position title should be blank

  @regression
  Scenario: Position titles are not duplicated
    Then there should be no duplicate position titles

  @bug
  Scenario: All locations contain "Istanbul, Turkey"
    Then all job locations should contain "Istanbul, Turkey"

  @bug
  Scenario: Location values are in title case not all-caps
    Then no location should be displayed in all-caps

  @bug
  Scenario: No QA job is listed outside Istanbul
    Then no job should be located outside Istanbul

  @regression
  Scenario: Lever URL is filtered by QA team
    Then the page URL should contain the Quality Assurance team filter

  @regression
  Scenario: All commitment types are Full-Time
    Then all positions should have Full-Time commitment
