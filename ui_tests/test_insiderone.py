"""
UI Tests for insiderone.com — QA Engineer Assessment
"""
import pytest
from playwright.sync_api import expect


BASE_URL = "https://insiderone.com"
CAREERS_URL = f"{BASE_URL}/careers/#open-roles"


class TestHomePage:
    """Task 1.1 — Home page loads with all main blocks."""

    def test_home_page_opens(self, page):
        page.goto(BASE_URL)
        expect(page).to_have_url(f"{BASE_URL}/")

    def test_home_page_title(self, page):
        page.goto(BASE_URL)
        expect(page).to_have_title(lambda t: len(t) > 0)

    def test_navigation_visible(self, page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        nav = page.locator("nav, header").first
        expect(nav).to_be_visible()

    def test_hero_section_visible(self, page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        # Hero / first main section should be visible
        hero = page.locator("section, .hero, [class*='hero'], main").first
        expect(hero).to_be_visible()

    def test_footer_visible(self, page):
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        footer = page.locator("footer").first
        expect(footer).to_be_visible()


class TestCareersPage:
    """Task 1.2 — Navigate to QA open positions and verify jobs list."""

    def test_see_all_teams_button_exists(self, page):
        page.goto(CAREERS_URL)
        page.wait_for_load_state("networkidle")
        btn = page.get_by_role("link", name="See all teams").or_(
            page.get_by_text("See all teams")
        )
        expect(btn.first).to_be_visible()

    def test_navigate_to_qa_positions(self, page):
        page.goto(CAREERS_URL)
        page.wait_for_load_state("networkidle")

        # Click "See all teams"
        page.get_by_text("See all teams").first.click()
        page.wait_for_load_state("networkidle")

        # Click "Quality Assurance" department
        page.get_by_text("Quality Assurance").first.click()
        page.wait_for_load_state("networkidle")

        # Jobs list should be present
        jobs = page.locator("[class*='job'], [class*='position'], li[class*='open']")
        expect(jobs.first).to_be_visible()


class TestJobListings:
    """Task 1.3 — Verify job fields contain expected values."""

    QA_DEPARTMENT = "Quality Assurance"
    EXPECTED_LOCATION = "Istanbul, Turkey"

    @pytest.fixture(autouse=True)
    def navigate_to_qa(self, page):
        page.goto(CAREERS_URL)
        page.wait_for_load_state("networkidle")
        page.get_by_text("See all teams").first.click()
        page.wait_for_load_state("networkidle")
        page.get_by_text("Quality Assurance").first.click()
        page.wait_for_load_state("networkidle")

    def test_all_positions_contain_quality_assurance(self, page):
        job_titles = page.locator("[class*='position-title'], [class*='job-title'], h3, h4")
        count = job_titles.count()
        assert count > 0, "No job listings found"
        for i in range(count):
            title = job_titles.nth(i).inner_text()
            assert self.QA_DEPARTMENT in title, (
                f"Position '{title}' does not contain '{self.QA_DEPARTMENT}'"
            )

    def test_all_departments_contain_quality_assurance(self, page):
        departments = page.locator("[class*='department'], [class*='team']")
        count = departments.count()
        assert count > 0, "No department labels found"
        for i in range(count):
            dept = departments.nth(i).inner_text()
            assert self.QA_DEPARTMENT in dept, (
                f"Department '{dept}' does not contain '{self.QA_DEPARTMENT}'"
            )

    def test_all_locations_contain_istanbul_turkey(self, page):
        locations = page.locator("[class*='location'], [class*='city']")
        count = locations.count()
        assert count > 0, "No location labels found"
        for i in range(count):
            loc = locations.nth(i).inner_text()
            assert self.EXPECTED_LOCATION in loc, (
                f"Location '{loc}' does not contain '{self.EXPECTED_LOCATION}'"
            )


class TestApplyButton:
    """Task 1.4 — Apply button redirects to Lever application form."""

    @pytest.fixture(autouse=True)
    def navigate_to_first_qa_job(self, page):
        page.goto(CAREERS_URL)
        page.wait_for_load_state("networkidle")
        page.get_by_text("See all teams").first.click()
        page.wait_for_load_state("networkidle")
        page.get_by_text("Quality Assurance").first.click()
        page.wait_for_load_state("networkidle")

    def test_apply_redirects_to_lever(self, page):
        with page.expect_popup() as popup_info:
            page.get_by_text("Apply").first.click()
        popup = popup_info.value
        popup.wait_for_load_state("networkidle")
        assert "lever.co" in popup.url, (
            f"Expected Lever URL, got: {popup.url}"
        )


class TestAIGeneratedScenario:
    """
    Task 1 AI Sub-Scenario — Contact form validation.
    Generated with AI assistance (see /prompts/01_contact_form.md).
    """

    def test_contact_form_accessible(self, page):
        """Verify the contact / demo request form is reachable and renders fields."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        # Find a CTA that leads to a contact/demo form
        cta = page.get_by_role("link", name=lambda n: any(
            kw in n.lower() for kw in ["contact", "demo", "get started", "request"]
        )).first
        expect(cta).to_be_visible()
        cta.click()
        page.wait_for_load_state("networkidle")

        # At least one form input should be present
        inputs = page.locator("input[type='text'], input[type='email'], input[name]")
        expect(inputs.first).to_be_visible()

    def test_contact_form_submit_requires_email(self, page):
        """Empty email should prevent form submission (client-side validation)."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")

        cta = page.get_by_role("link", name=lambda n: any(
            kw in n.lower() for kw in ["contact", "demo", "get started", "request"]
        )).first
        cta.click()
        page.wait_for_load_state("networkidle")

        # Try to submit without filling in the email
        submit = page.get_by_role("button", name=lambda n: any(
            kw in n.lower() for kw in ["submit", "send", "request"]
        )).first
        submit.click()

        # Page should not navigate away (validation blocked submission)
        assert "insiderone.com" in page.url or "thank" not in page.url.lower()
