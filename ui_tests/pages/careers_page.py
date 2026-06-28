import re
from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError


class CareersPage:
    URL = "https://insiderone.com/careers/#open-roles"

    def __init__(self, page: Page):
        self.page = page

    # --- Navigation ---

    def goto(self):
        # This page never reaches 'networkidle' — a background script (chat
        # widget / analytics) keeps polling indefinitely. domcontentloaded +
        # an explicit wait for the section we need is reliable instead.
        self.page.goto(self.URL, wait_until="domcontentloaded", timeout=30000)
        self.open_roles_section().wait_for(state="visible", timeout=10000)

    def reveal_all_teams(self, retries: int = 3):
        """Click 'See all teams' to expand the hidden department cards.

        Two independent sources of flakiness on this page, neither a local
        bug: (1) on the first page visited in the browser context, the
        cookie consent overlay can still be covering the button, so the
        click uses force=True to bypass occlusion checks rather than
        clicking the real "Accept All" button (which would write a
        consent cookie shared by the whole context and break the
        home_page "fresh visit" cookie banner test). (2) card hrefs are
        placeholders ("#") until a background AJAX call hydrates them
        with the real Lever URL, and that hydration occasionally never
        fires for a given page load — retry with a fresh reload instead
        of just waiting longer.
        """
        for attempt in range(retries):
            try:
                self.page.get_by_text("See all teams", exact=True).first.click(
                    force=True, timeout=12000
                )
                self.page.wait_for_function(
                    "() => { const el = document.querySelector("
                    "\"[data-department='Quality Assurance'] .insiderone-icon-cards-grid-item-btn\""
                    "); return el && el.href.includes('lever'); }",
                    timeout=12000,
                )
                return
            except PlaywrightTimeoutError:
                if attempt == retries - 1:
                    raise
                self.goto()

    def click_qa_positions(self):
        """Click the QA card button → navigates to Lever."""
        self.qa_card_button().click(force=True)
        self.page.wait_for_load_state("domcontentloaded")

    # --- Locators ---

    def title(self) -> str:
        return self.page.title()

    def open_roles_section(self) -> Locator:
        return self.page.locator("#open-roles")

    def see_all_teams_button(self) -> Locator:
        return self.page.get_by_text("See all teams", exact=True).first

    def department_card(self, department: str) -> Locator:
        return self.page.locator(f"[data-department='{department}']")

    def qa_card(self) -> Locator:
        return self.department_card("Quality Assurance")

    def qa_card_button(self) -> Locator:
        return self.qa_card().locator(".insiderone-icon-cards-grid-item-btn")

    def all_cards(self) -> list[Locator]:
        return self.page.locator(".insiderone-icon-cards-grid-item").all()

    def card_position_count(self, card: Locator) -> int:
        text = card.locator(".insiderone-icon-cards-grid-item-btn").inner_text().strip()
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else 0

    def card_lever_href(self, card: Locator) -> str:
        return card.locator(".insiderone-icon-cards-grid-item-btn").get_attribute("href") or ""

    def current_url(self) -> str:
        return self.page.url
