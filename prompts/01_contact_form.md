# Prompt Iteration 01 — AI-Generated UI Test Scenario

## Goal
Generate an additional UI test scenario for insiderone.com that goes beyond the
careers-page flow and tests another meaningful user interaction.

## Context provided
- Framework: Playwright + pytest
- Existing tests cover: homepage load, careers page navigation, job listing validation, Apply redirect
- Page structure: insiderone.com is a B2B SaaS marketing site with a "Request a Demo" / contact CTA

## Prompt
> "Using Playwright and pytest, generate a UI test class that verifies the contact
> or demo-request form on insiderone.com is accessible and enforces basic
> client-side validation (e.g., empty email prevents submission). The class should
> follow the same fixture pattern as the existing conftest.py (page fixture, headless
> browser). Include two test methods: one that verifies the form renders with at
> least one input field, and one that verifies an empty submission does not navigate
> away from the page."

## Output evaluation
**Accepted:**
- Two-method structure (form accessible + submit validation)
- Using `page.get_by_role` and lambda name matching to avoid hard-coding selectors
- Asserting page URL stays on insiderone.com after failed submit

**Rejected / refined:**
- AI initially used `page.locator("form")` with a hard-coded form index — replaced
  with role-based selectors to be more resilient to DOM changes
- AI assumed a specific button text "Submit" — replaced with a lambda that matches
  multiple common CTA labels
- AI used `time.sleep()` for waits — replaced with `wait_for_load_state("networkidle")`

## Iteration notes
Second prompt added: "Avoid hard-coded selectors and time.sleep; use Playwright's
built-in waiting mechanisms and role-based locators." This produced the cleaner
version that was committed.
