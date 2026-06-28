import re
from playwright.sync_api import Page, Locator


class HomePage:
    URL = "https://insiderone.com/"
    EXPECTED_TITLE = "Insider One | #1 Platform for AI-Powered Customer Engagement"
    EXPECTED_H1 = "The leading"

    def __init__(self, page: Page):
        self.page = page

    # --- Navigation ---

    def goto(self):
        self.page.goto(self.URL, wait_until="networkidle")

    # --- Locators ---

    def title(self) -> str:
        return self.page.title()

    def url(self) -> str:
        return self.page.url

    def h1(self) -> Locator:
        return self.page.locator("h1").first

    def logo(self) -> Locator:
        return self.page.locator("header img, nav img, a[href='/'] img").first

    def main_menu(self) -> Locator:
        return self.page.locator(".header-menu-list")

    def nav_item(self, name: str) -> Locator:
        return self.main_menu().get_by_text(name, exact=True).first

    def cta_get_a_demo(self) -> Locator:
        return self.page.get_by_role("link", name=re.compile(r"get a demo", re.IGNORECASE)).first

    def cta_platform_tour(self) -> Locator:
        return self.page.get_by_role("link", name=re.compile(r"platform tour", re.IGNORECASE)).first

    def login_link(self) -> Locator:
        return self.page.get_by_role("link", name=re.compile(r"login", re.IGNORECASE)).first

    def footer(self) -> Locator:
        return self.page.locator("footer").first

    def cookie_banner(self) -> Locator:
        return self.page.get_by_text("Cookies are used", exact=False).first

    def cookie_accept_button(self) -> Locator:
        return self.page.get_by_role("button", name=re.compile(r"accept all", re.IGNORECASE)).first

    def language_button(self) -> Locator:
        return self.page.get_by_text("English", exact=True).first

    def language_option(self, locale: str) -> Locator:
        return self.page.get_by_text(locale, exact=True).first

    def clickable_language_option(self, locale: str) -> Locator:
        """Each locale's text is rendered twice (desktop + mobile nav
        variants), only one of which is visible/clickable at a given
        viewport. `language_option()` above just checks presence via
        `.first`, which is fine for "does this exist" but not safe to
        click — `.first` isn't guaranteed to be the visible copy."""
        candidates = self.page.get_by_text(locale, exact=True)
        for i in range(candidates.count()):
            candidate = candidates.nth(i)
            if candidate.is_visible():
                return candidate
        return candidates.first

    def switch_language_to(self, locale: str):
        self.language_button().click()
        self.clickable_language_option(locale).click()

    def careers_nav_link(self) -> Locator:
        """Matched by href, not link text — the visible text changes per
        locale ("Careers" / "Carrières"), the href is the stable anchor."""
        return self.page.locator('a[href*="/careers"]').first

    def follow_careers_link(self):
        self.careers_nav_link().click()

    def meta_description(self) -> str:
        return self.page.locator('meta[name="description"]').get_attribute("content") or ""

    def broken_images(self) -> list[str]:
        # Excludes 1x1 tracking/analytics pixels — their load success depends
        # on third-party ad-tech infrastructure, not this site's content,
        # and is too flaky to be a meaningful "broken image" signal.
        return self.page.evaluate("""() =>
            [...document.images]
                .filter(img => !img.naturalWidth && img.width > 1 && img.height > 1)
                .map(img => img.src)
        """)
