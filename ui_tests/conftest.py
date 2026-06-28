"""
Root conftest — browser session shared across all tests.
Browser opens once per pytest run; each scenario gets its own page (tab).

The Playwright instance itself is owned by the pytest-playwright plugin's
own `browser` fixture (it manages launch args, --headed, etc.) — starting a
second sync_playwright() here would conflict with it and break every test.
"""
import pytest
from playwright.sync_api import Browser, BrowserContext


@pytest.fixture(scope="session")
def browser_context(browser: Browser) -> BrowserContext:
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    yield context
    context.close()
