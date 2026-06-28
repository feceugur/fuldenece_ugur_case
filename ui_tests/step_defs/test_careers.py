import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect

from pages.careers_page import CareersPage

scenarios("../features/careers.feature")


@given("I am on the Insider One careers page")
def go_to_careers(careers_page: CareersPage):
    careers_page.goto()


@then("the careers page title should contain \"career\"")
def check_careers_title(careers_page: CareersPage):
    assert "career" in careers_page.title().lower(), \
        f"Careers page title unexpected: {careers_page.title()!r}"


@then("the open roles section should be visible")
def check_open_roles(careers_page: CareersPage):
    expect(careers_page.open_roles_section()).to_be_visible()


@then('the "See all teams" button should be visible')
def check_see_all_teams(careers_page: CareersPage):
    expect(careers_page.see_all_teams_button()).to_be_visible()


@then('the "See all teams" button href should not be an external URL')
def check_see_all_teams_href(careers_page: CareersPage):
    href = careers_page.see_all_teams_button().get_attribute("href") or ""
    assert "javascript" in href or href.startswith("#") or href == "", \
        f"'See all teams' points to unexpected external URL: {href!r}"


@when('I click "See all teams"')
def click_see_all_teams(careers_page: CareersPage):
    careers_page.reveal_all_teams()


@then(parsers.parse('the "{department}" department card should be visible'))
def check_department_card(careers_page: CareersPage, department: str):
    expect(careers_page.department_card(department)).to_be_visible(timeout=8000)


@then(parsers.parse('the "{department}" card should show more than 0 open positions'))
def check_open_positions(careers_page: CareersPage, department: str):
    count = careers_page.card_position_count(careers_page.department_card(department))
    assert count > 0, f"'{department}' card shows 0 open positions"


@then(parsers.parse('the "{department}" card button should link to Lever with team filter "{filter_value}"'))
def check_lever_link(careers_page: CareersPage, department: str, filter_value: str):
    href = careers_page.card_lever_href(careers_page.department_card(department))
    assert "lever.co" in href, f"QA button does not point to Lever: {href!r}"
    assert filter_value in href or filter_value.replace("%20", "+") in href, \
        f"Lever URL missing team filter '{filter_value}': {href!r}"


@when('I click the "Quality Assurance" open positions button')
def click_qa_button(careers_page: CareersPage):
    careers_page.click_qa_positions()


@then(parsers.parse('I should be on a Lever page filtered for "{keyword}" Assurance'))
def check_lever_url(careers_page: CareersPage, keyword: str):
    url = careers_page.current_url()
    assert "lever.co" in url, f"Not on Lever page: {url}"
    assert keyword in url, f"Lever URL missing '{keyword}': {url}"


@then("cards with 0 open positions should not have a team-filtered Lever URL")
def check_zero_position_cards(careers_page: CareersPage):
    failures = []
    for card in careers_page.all_cards():
        count = careers_page.card_position_count(card)
        href = careers_page.card_lever_href(card)
        if count == 0 and "team=" in href:
            failures.append(href)
    assert failures == [], \
        f"0-position cards with team-filtered URLs: {failures}"
