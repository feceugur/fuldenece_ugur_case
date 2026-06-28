# Prompt Iteration 04 — Language Switch + Navigation Persistence (insiderone.com)

This is the required **AI-Augmented Sub-Scenario** for Task 1, plus one
revision requested after the first round. Two iterations are logged below.

### Why this scenario, and not a contact-form test
An earlier draft of this sub-scenario (since removed) targeted a contact /
demo-request form on insiderone.com. That idea was dropped once it was
checked against the actual current homepage: there is no inline contact
form — "Get a demo" is just a link to elsewhere, and its visibility is
already covered by an existing scenario. There was nothing distinct left to
test there, so the sub-scenario was redirected to the language switcher
instead, which had a real, verifiable gap (see Iteration 1 below).

## Iteration 1 — Does the language switcher actually switch the language?

### Goal
The existing `home_page.feature` scenario ("Language switcher shows expected
locales") only checks that the dropdown *displays* "English / Français /
Español" — it never clicks an option or checks that anything actually
changes. Generate one additional UI scenario that tests the switch itself,
not just its presence.

### Context provided
- Existing `home_page.feature` / `home_page.py` / `test_home_page.py`
  conventions (Background + tagged Scenarios, Page Object Model, pytest-bdd
  `parsers.parse` steps).
- The existing `language_button()` / `language_option(locale)` locators in
  `pages/home_page.py`.
- No assumption about the site's actual switching mechanism (URL change?
  AJAX content swap? modal?) — this had to be investigated live, not guessed.

### Prompt
> "Add a UI test scenario for insiderone.com's language switcher that
> actually clicks a locale option (not just checks it's listed) and verifies
> the switch took effect. Investigate the live site first to find out what
> 'took effect' should mean — don't assume the mechanism."

### Investigation (before writing any assertion)
- Opening the switcher and clicking "Français" navigates to
  `https://insiderone.com/fr/` (full navigation, not an AJAX swap) — the
  `<title>` and `<h1>` are translated server-side.
- `get_by_text(locale, exact=True)` matches **two** elements per locale
  (a desktop and a mobile nav variant); `.first` is not guaranteed to be the
  visible/clickable one at a given viewport.

### Output evaluation
**Accepted:**
- Asserting on `page.url` containing `/fr/` and the title changing from the
  known English title — both are real, server-rendered signals, not
  implementation details that could change without the user noticing.

**Rejected / refined:**
- A first draft reused the existing `language_option(locale)` locator
  (`.first`, no visibility check) to perform the click. Rejected — it
  happened to work in manual testing but isn't safe, since `.first` could
  resolve to the hidden mobile-nav duplicate depending on DOM order. Added
  a separate `clickable_language_option(locale)` that filters for
  `is_visible()` explicitly, instead of changing the existing locator's
  behavior (which is still used by the older "shows expected locales"
  check and didn't need to change).

### Result
`ui_tests/features/home_page.feature` — new scenario "Switching language via
the switcher navigates to the localized page", tagged `@ai_augmented`.

---

## Iteration 2 — Revision requested: does the switch survive navigation?

### Goal
Following the user's request: extend the scenario above to check whether
switching language changes more than just the current page — specifically,
whether navigating to a *different* page afterward keeps the chosen locale,
and whether all interactive elements (not just the page you switched on)
respect it.

### Context provided
- Iteration 1's findings (URL-based switching, `/fr/` prefix).
- The existing `careers_page.py` / careers flow, as a second, independent
  page to navigate to and check.

### Investigation
- From the French homepage, the in-page "Carrières" nav link's `href` is
  `/fr/careers/` — the locale prefix is carried into the link itself, not
  just the current URL. Navigating there lands on a fully French careers
  page (`title`: "Insider One Carrières | Trouvez votre prochaine
  opportunité").
- While checking *every* piece of header chrome for translation, the
  "Login" link was the one exception: it stays in English ("Login") on the
  French page, while the nav items, the careers link, and the page title
  all translate correctly.

### Output evaluation
**Accepted:**
- A new scenario asserting the careers link's `href`/destination stays
  under `/fr/` after navigating — locator matches on `href*="/careers"`
  rather than link text, since the visible text itself changes per locale
  and shouldn't be the thing being matched against.
- A second new scenario, tagged `@bug` (matching this project's existing
  convention of describing the *correct* behavior positively and letting
  the assertion fail to document the gap — see `job_listings.feature`):
  the login link should not still say "Login" after switching to French.
  This wasn't something I went looking for; it surfaced from systematically
  checking each header element for translation while validating the
  persistence scenario.

**Rejected:**
- Considered testing Spanish (`/es/`) too, for symmetry — skipped to keep
  scope tight, since French alone is enough to prove both "switch persists
  across navigation" and "one element is inconsistently translated"; adding
  a second locale would duplicate the same two assertions without adding a
  new failure mode.

### Result
Two more scenarios in `ui_tests/features/home_page.feature`, both tagged
`@ai_augmented`:
- "Navigating to another page after switching language keeps the locale"
  (`@regression`) — passes.
- "Login link is translated when the page is in French" (`@bug`) — fails on
  purpose, documenting a real, found inconsistency.

All three scenarios from both iterations were run against the live site and
confirmed: 3 passed (switch works, persists across navigation), 1 failed as
expected (login link not translated).
