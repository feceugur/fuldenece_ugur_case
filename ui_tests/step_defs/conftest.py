"""
step_defs/conftest.py — scenario-scoped page + shared step fixtures.
'page' is function-scoped so each scenario gets a clean tab.
"""
import pytest
from playwright.sync_api import Page

from pages.home_page import HomePage
from pages.careers_page import CareersPage
from pages.lever_page import LeverPage


@pytest.fixture
def page(browser_context) -> Page:
    """New browser tab per scenario; closed after scenario completes."""
    p = browser_context.new_page()
    yield p
    p.close()


# --- Page Object fixtures ---

@pytest.fixture
def home_page(page) -> HomePage:
    return HomePage(page)


@pytest.fixture
def careers_page(page) -> CareersPage:
    return CareersPage(page)


@pytest.fixture
def lever_page(page) -> LeverPage:
    return LeverPage(page)
