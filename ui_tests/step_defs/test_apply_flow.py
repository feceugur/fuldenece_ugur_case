import re
import pytest
from pytest_bdd import scenarios, given, when, then
from playwright.sync_api import expect

from pages.lever_page import LeverPage

scenarios("../features/apply_flow.feature")


@given("I am on the Lever QA jobs page")
def go_to_lever_qa(lever_page: LeverPage):
    lever_page.goto_qa_jobs()


@then("all Apply button hrefs should match the Lever job URL pattern")
def check_apply_url_format(lever_page: LeverPage):
    failures = []
    for posting in lever_page.all_postings():
        title = lever_page.posting_title(posting)
        href = lever_page.posting_apply_href(posting)
        if not lever_page.posting_apply_url_is_valid(posting):
            failures.append((title, href))
    assert failures == [], (
        "Apply URLs with unexpected format:\n" +
        "\n".join(f"  - {t!r} → {h!r}" for t, h in failures)
    )


@when("I click the Apply button on the first Istanbul posting")
def click_apply(lever_page: LeverPage):
    posting = lever_page.first_istanbul_posting()
    if posting is None:
        pytest.skip("No Istanbul-based posting found")
    href = lever_page.posting_apply_href(posting)
    lever_page.page.goto(href, wait_until="domcontentloaded", timeout=60000)


@then("I should be on a Lever job page for Insider One")
def check_lever_job_page(lever_page: LeverPage):
    url = lever_page.current_url()
    assert "lever.co" in url, f"Not on Lever: {url}"
    assert "/insiderone/" in url, f"Not on InsiderOne job: {url}"


@when("I navigate to the apply form of the first Istanbul posting")
def go_to_apply_form(lever_page: LeverPage):
    posting = lever_page.first_istanbul_posting()
    if posting is None:
        pytest.skip("No Istanbul-based posting found")
    apply_url = lever_page.posting_apply_href(posting)
    lever_page.goto_apply(apply_url)


@then("the application form should have a name field")
def check_name_field(lever_page: LeverPage):
    expect(lever_page.form_name_input()).to_be_visible(timeout=10000)


@then("the application form should have an email field")
def check_email_field(lever_page: LeverPage):
    expect(lever_page.form_email_input()).to_be_visible()


@then("the application form should have a resume upload field")
def check_resume_field(lever_page: LeverPage):
    expect(lever_page.form_resume_input()).to_be_attached()


@then("the apply page title should not be empty")
def check_apply_title(lever_page: LeverPage):
    assert lever_page.page.title().strip() != "", "Apply page title is empty"


@then("all Apply button hrefs should be unique")
def check_unique_apply_hrefs(lever_page: LeverPage):
    hrefs = [lever_page.posting_apply_href(p) for p in lever_page.all_postings()]
    dupes = [h for h in hrefs if hrefs.count(h) > 1]
    assert dupes == [], f"Duplicate Apply URLs: {list(set(dupes))}"
