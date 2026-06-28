@home
Feature: Insider One Home Page
  As a visitor
  I want to see a fully loaded and functional home page
  So that I can trust the platform and navigate the site

  Background:
    Given I am on the Insider One home page

  @smoke
  Scenario: Page title is correct
    Then the page title should be correct

  @smoke
  Scenario: Page URL is canonical
    Then the URL should end with "/"

  @smoke
  Scenario: H1 heading is visible and contains expected text
    Then the H1 should contain "The leading"

  @smoke
  Scenario: Logo is visible in the header
    Then the logo should be visible

  @smoke
  Scenario: Main navigation items are present
    Then the main menu should contain "Platform"
    And the main menu should contain "Industries"
    And the main menu should contain "Customers"
    And the main menu should contain "Resources"

  @smoke
  Scenario: Primary CTA buttons are visible
    Then the "Get a demo" CTA should be visible
    And the "Platform Tour" CTA should be visible

  @smoke
  Scenario: Login link is visible in the header
    Then the login link should be visible

  @smoke
  Scenario: Footer is rendered
    Then the footer should be visible

  @regression
  Scenario: Page has no broken images
    Then there should be no broken images

  @regression @gdpr
  Scenario: Cookie consent banner appears on fresh visit
    Then the cookie banner should be visible

  @regression @gdpr
  Scenario: Accepting cookies dismisses the banner
    When I accept the cookie banner
    Then the cookie banner should not be visible

  @regression
  Scenario: Meta description is present and not empty
    Then the meta description should be present

  @regression
  Scenario: Language switcher shows expected locales
    Then the language switcher should show "English"
    And the language switcher should show "Français"
    And the language switcher should show "Español"

  @regression @ai_augmented
  Scenario: Switching language via the switcher navigates to the localized page
    When I switch the language to "Français"
    Then the page URL should contain "/fr/"
    And the page title should no longer be the English title

  @regression @ai_augmented
  Scenario: Navigating to another page after switching language keeps the locale
    When I switch the language to "Français"
    And I follow the careers link
    Then the page URL should contain "/fr/careers/"
    And the page title should no longer be the English title

  @bug @ai_augmented
  Scenario: Login link is translated when the page is in French
    When I switch the language to "Français"
    Then the login link should not say "Login"
