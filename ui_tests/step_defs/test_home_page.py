import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect

from pages.home_page import HomePage

scenarios("../features/home_page.feature")


@given("I am on the Insider One home page")
def go_to_home(home_page: HomePage):
    home_page.goto()


@then("the page title should be correct")
def check_title(home_page: HomePage):
    assert home_page.title() == HomePage.EXPECTED_TITLE, \
        f"Title mismatch. Got: {home_page.title()!r}"


@then(parsers.parse('the URL should end with "{suffix}"'))
def check_url_suffix(home_page: HomePage, suffix: str):
    assert home_page.url().endswith(suffix), \
        f"URL does not end with '{suffix}': {home_page.url()!r}"


@then(parsers.parse('the H1 should contain "{text}"'))
def check_h1(home_page: HomePage, text: str):
    h1 = home_page.h1()
    expect(h1).to_be_visible()
    assert text in h1.inner_text(), \
        f"H1 does not contain '{text}': {h1.inner_text()!r}"


@then("the logo should be visible")
def check_logo(home_page: HomePage):
    expect(home_page.logo()).to_be_visible()


@then(parsers.parse('the main menu should contain "{item}"'))
def check_nav_item(home_page: HomePage, item: str):
    expect(home_page.nav_item(item)).to_be_visible(timeout=5000)


@then(parsers.parse('the "{cta_name}" CTA should be visible'))
def check_cta(home_page: HomePage, cta_name: str):
    if cta_name == "Get a demo":
        expect(home_page.cta_get_a_demo()).to_be_visible()
    elif cta_name == "Platform Tour":
        expect(home_page.cta_platform_tour()).to_be_visible()


@then("the login link should be visible")
def check_login(home_page: HomePage):
    expect(home_page.login_link()).to_be_visible()


@then("the footer should be visible")
def check_footer(home_page: HomePage):
    expect(home_page.footer()).to_be_visible()


@then("there should be no broken images")
def check_broken_images(home_page: HomePage):
    broken = home_page.broken_images()
    assert broken == [], f"Broken images found: {broken}"


@then("the cookie banner should be visible")
def check_cookie_banner_visible(home_page: HomePage):
    expect(home_page.cookie_banner()).to_be_visible(timeout=8000)


@when("I accept the cookie banner")
def accept_cookies(home_page: HomePage):
    btn = home_page.cookie_accept_button()
    if btn.is_visible():
        btn.click()


@then("the cookie banner should not be visible")
def check_cookie_banner_gone(home_page: HomePage):
    expect(home_page.cookie_accept_button()).not_to_be_visible(timeout=5000)


@then("the meta description should be present")
def check_meta(home_page: HomePage):
    desc = home_page.meta_description()
    assert len(desc) > 20, f"Meta description missing or too short: {desc!r}"


@then(parsers.parse('the language switcher should show "{locale}"'))
def check_locale(home_page: HomePage, locale: str):
    el = home_page.language_option(locale)
    assert el.count() > 0, f"Locale '{locale}' not found in language switcher"


@when(parsers.parse('I switch the language to "{locale}"'))
def switch_language(home_page: HomePage, locale: str):
    home_page.switch_language_to(locale)


@then(parsers.parse('the page URL should contain "{fragment}"'))
def check_url_contains(home_page: HomePage, fragment: str):
    assert fragment in home_page.url(), \
        f"Expected URL to contain {fragment!r}, got {home_page.url()!r}"


@then("the page title should no longer be the English title")
def check_title_translated(home_page: HomePage):
    assert home_page.title() != HomePage.EXPECTED_TITLE, \
        "Page title is unchanged after switching language — the switch may not have taken effect"


@when("I follow the careers link")
def follow_careers_link(home_page: HomePage):
    home_page.follow_careers_link()


@then(parsers.parse('the login link should not say "{text}"'))
def check_login_link_translated(home_page: HomePage, text: str):
    """BUG: the login link stays in English ("Login") on every locale —
    every other piece of chrome (nav items, careers link, page title)
    translates, this one doesn't."""
    actual = home_page.login_link().inner_text().strip()
    assert actual != text, \
        f"Login link is still {actual!r} after switching language — not translated like the rest of the nav"
