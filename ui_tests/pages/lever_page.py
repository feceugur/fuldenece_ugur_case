import re
from playwright.sync_api import Page, Locator


class LeverPage:
    QA_URL = "https://jobs.lever.co/insiderone?team=Quality%20Assurance"

    def __init__(self, page: Page):
        self.page = page

    # --- Navigation ---

    def goto_qa_jobs(self):
        self.page.goto(self.QA_URL, wait_until="networkidle")
        self.page.wait_for_timeout(2000)

    def goto_apply(self, apply_url: str):
        self.page.goto(apply_url + "/apply", wait_until="domcontentloaded", timeout=60000)
        self.page.wait_for_timeout(3000)

    # --- Job listing locators ---

    def all_postings(self) -> list[Locator]:
        return self.page.locator(".posting").all()

    def posting_title(self, posting: Locator) -> str:
        return posting.locator("h5[data-qa='posting-name']").inner_text().strip()

    def posting_location(self, posting: Locator) -> str:
        return posting.locator(".sort-by-location").inner_text().strip()

    def posting_commitment(self, posting: Locator) -> str:
        return posting.locator(".sort-by-commitment").inner_text().strip()

    def posting_apply_href(self, posting: Locator) -> str:
        return posting.locator("[data-qa='btn-apply'] a").get_attribute("href") or ""

    def apply_button(self, posting: Locator) -> Locator:
        return posting.locator("[data-qa='btn-apply'] a")

    def first_istanbul_posting(self) -> Locator | None:
        for posting in self.all_postings():
            if "ISTANBUL" in self.posting_location(posting).upper():
                return posting
        return None

    # --- Apply form locators ---

    def form_name_input(self) -> Locator:
        return self.page.locator("[data-qa='name-input']")

    def form_email_input(self) -> Locator:
        return self.page.locator("[data-qa='email-input']")

    def form_resume_input(self) -> Locator:
        return self.page.locator("[data-qa='input-resume']")

    def form_submit_button(self) -> Locator:
        return self.page.locator("[data-qa='btn-submit']")

    # --- Helpers ---

    def current_url(self) -> str:
        return self.page.url

    def posting_apply_url_is_valid(self, posting: Locator) -> bool:
        href = self.posting_apply_href(posting)
        return bool(re.match(
            r"https://jobs\.lever\.co/insiderone/[a-f0-9\-]{36}$", href
        ))
