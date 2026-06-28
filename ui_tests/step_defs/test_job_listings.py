import pytest
from pytest_bdd import scenarios, given, when, then
from playwright.sync_api import expect

from pages.lever_page import LeverPage

scenarios("../features/job_listings.feature")

EXPECTED_QA_DEPT = "Quality Assurance"
EXPECTED_LOCATION = "Istanbul, Turkey"


@given("I am on the Lever QA jobs page")
def go_to_lever_qa(lever_page: LeverPage):
    lever_page.goto_qa_jobs()


@then("there should be at least 1 job posting")
def check_postings_exist(lever_page: LeverPage):
    postings = lever_page.all_postings()
    assert len(postings) >= 1, "No QA job postings found on Lever"


@then("every posting should have a non-empty title")
def check_titles_not_empty(lever_page: LeverPage):
    for posting in lever_page.all_postings():
        title = lever_page.posting_title(posting)
        assert title != "", "A posting has an empty title"


@then("every posting should have an Apply button")
def check_apply_buttons(lever_page: LeverPage):
    for posting in lever_page.all_postings():
        btn = lever_page.apply_button(posting)
        assert btn.count() == 1, \
            f"Apply button missing on: {lever_page.posting_title(posting)!r}"
        expect(btn).to_be_visible()


@then("every posting should have a location")
def check_locations_exist(lever_page: LeverPage):
    for posting in lever_page.all_postings():
        loc = lever_page.posting_location(posting)
        assert loc != "", \
            f"Location missing on: {lever_page.posting_title(posting)!r}"


@then(f'all position titles should contain "Quality Assurance"')
def check_titles_contain_qa(lever_page: LeverPage):
    """
    BUG: 'Senior Software QA Engineer' and 'Software QA Engineer - Europe'
    use the abbreviation 'QA' instead of 'Quality Assurance'.
    """
    failures = []
    for posting in lever_page.all_postings():
        title = lever_page.posting_title(posting)
        if EXPECTED_QA_DEPT not in title:
            failures.append(title)
    assert failures == [], (
        f"Positions missing '{EXPECTED_QA_DEPT}' in title:\n" +
        "\n".join(f"  - {t!r}" for t in failures)
    )


@then("no position title should be blank")
def check_no_blank_titles(lever_page: LeverPage):
    for posting in lever_page.all_postings():
        assert lever_page.posting_title(posting) != "", "Blank title found"


@then("there should be no duplicate position titles")
def check_no_duplicate_titles(lever_page: LeverPage):
    titles = [lever_page.posting_title(p) for p in lever_page.all_postings()]
    dupes = [t for t in set(titles) if titles.count(t) > 1]
    assert dupes == [], f"Duplicate job titles: {dupes}"


@then(f'all job locations should contain "Istanbul, Turkey"')
def check_locations_istanbul(lever_page: LeverPage):
    """
    BUG: Lever shows 'ISTANBUL' (no country, all-caps).
    One job shows Berlin/Europe — not Istanbul at all.
    """
    failures = []
    for posting in lever_page.all_postings():
        title = lever_page.posting_title(posting)
        loc = lever_page.posting_location(posting)
        if EXPECTED_LOCATION.upper() not in loc.upper():
            failures.append((title, loc))
    assert failures == [], (
        f"Jobs not in '{EXPECTED_LOCATION}':\n" +
        "\n".join(f"  - {t!r} → {l!r}" for t, l in failures)
    )


@then("no location should be displayed in all-caps")
def check_location_casing(lever_page: LeverPage):
    """BUG: All locations rendered in ALL CAPS by Lever."""
    failures = []
    for posting in lever_page.all_postings():
        loc = lever_page.posting_location(posting)
        if loc == loc.upper():
            failures.append(loc)
    assert failures == [], \
        f"All-caps location values (formatting bug): {list(set(failures))}"


@then("no job should be located outside Istanbul")
def check_no_non_istanbul_jobs(lever_page: LeverPage):
    """BUG: 'Software QA Engineer - Europe' is listed in Berlin."""
    failures = []
    for posting in lever_page.all_postings():
        title = lever_page.posting_title(posting)
        loc = lever_page.posting_location(posting).upper()
        if "ISTANBUL" not in loc:
            failures.append((title, loc))
    assert failures == [], (
        "QA jobs outside Istanbul:\n" +
        "\n".join(f"  - {t!r} → {l!r}" for t, l in failures)
    )


@then("the page URL should contain the Quality Assurance team filter")
def check_url_filter(lever_page: LeverPage):
    url = lever_page.current_url()
    assert "team=Quality%20Assurance" in url or "team=Quality+Assurance" in url, \
        f"Lever URL not filtered by QA team: {url}"


@then("all positions should have Full-Time commitment")
def check_full_time(lever_page: LeverPage):
    failures = []
    for posting in lever_page.all_postings():
        title = lever_page.posting_title(posting)
        commitment = lever_page.posting_commitment(posting)
        if "full" not in commitment.lower():
            failures.append((title, commitment))
    assert failures == [], (
        "Non-full-time QA jobs:\n" +
        "\n".join(f"  - {t!r} → {c!r}" for t, c in failures)
    )
