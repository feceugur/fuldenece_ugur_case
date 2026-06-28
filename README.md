# QA Engineer Assessment

Three-part test project covering UI automation, load testing, and API testing.

## Run it

```bash
git clone https://github.com/feceugur/fuldenece_ugur_case.git
cd fuldenece_ugur_case
python3 -m pip install -r requirements.txt
python3 run_all_tests.py
```

Useful variants:
```bash
python3 run_all_tests.py --skip-load          # UI + API only, fast
python3 run_all_tests.py --load-duration 30s  # shorter load test
```

## How This Was Built

This was built as an iterative human + AI pairing, not a single generated pass:

- **Structure and scope were set upfront, by me**: three self-contained
  directories (`ui_tests/`, `load_tests/`, `api_tests/`), one per assignment
  task, each with its own fixtures/config so any one of them can be reviewed
  or run in isolation. The BDD + Page Object Model layering for Task 1 and
  the thin HTTP-client wrapper for Task 3 (`PetstoreClient`, deliberately
  mirroring the POM pattern) were direction I gave, not something generated
  and accepted as-is.
- **Technology choices were discussed, not defaulted to**: Locust over
  JMeter for Task 2, specifically to keep the whole suite in one language
  and runnable with one `pip install`; Playwright + pytest-bdd over a
  page-script style for Task 1, to keep Gherkin scenarios readable as the
  actual spec.
- **The bug list below is not a checklist reverse-engineered into tests.**
  Every entry was found by running the suite against the live sites,
  reviewing the failure, and deciding whether it was a real site/API defect
  (kept, documented, `@bug`-tagged) or a test bug (fixed). Two defects were
  only caught this way:
  - **Real environment bug**, found by running the load test through VS
    Code's Run/Debug panel (the way a developer actually would) instead of
    a plain terminal: Locust's `gevent` concurrency model hangs
    indefinitely under `debugpy`. A terminal run always finished on time;
    only exercising the actual documented workflow surfaced it. Fixed by
    moving the load test to a `tasks.json` shell task instead of a debug
    launch config.
  - **Wrong hypothesis, corrected by data**: an early theory blamed search
    latency spikes on Turkish-character query encoding specifically.
    Running the load test several more times showed the spikes were random
    and endpoint-independent — the README and `prompts/02_load_test.md`
    were rewritten to match what was actually measured, not the first
    plausible story.

See `AI_USAGE.md` for the specifics of where AI output was accepted,
rejected, and reworked.

## Project Structure

```
CaseStudy/
├── ui_tests/                     # Task 1 — UI automation (target site under test)
│   ├── features/                # Gherkin BDD scenarios
│   │   ├── home_page.feature
│   │   ├── careers.feature
│   │   ├── job_listings.feature
│   │   └── apply_flow.feature
│   ├── pages/                   # Page Object Models
│   │   ├── home_page.py
│   │   ├── careers_page.py
│   │   └── lever_page.py
│   ├── step_defs/               # pytest-bdd step implementations
│   │   ├── conftest.py          # scenario-scoped page + POM fixtures
│   │   ├── test_home_page.py
│   │   ├── test_careers.py
│   │   ├── test_job_listings.py
│   │   └── test_apply_flow.py
│   └── conftest.py               # Root: session-scoped browser
├── load_tests/                   # Task 2 — n11.com search load test
│   └── locustfile.py
├── api_tests/                    # Task 3 — Petstore CRUD API tests
│   ├── clients/
│   │   └── petstore_client.py   # HTTP client wrapper (API equivalent of POM)
│   ├── conftest.py               # client / unique_id / pet_factory fixtures
│   └── test_petstore.py
├── prompts/
│   ├── 02_load_test.md          # Task 2 load-test redesign + bug investigation
│   ├── 03_load_test_debugpy_hang.md  # Task 2 debugging session (VS Code hang)
│   └── 04_language_switch.md    # Task 1 AI-Augmented Sub-Scenario (2 iterations)
├── .vscode/
│   ├── launch.json               # Debug configs: UI tests, API tests (headed/headless)
│   └── tasks.json                # Load test task (run as plain shell, not debugpy — see prompts/03_*)
├── run_all_tests.py              # Single-command runner: installs Chromium, runs all 3 tasks, writes report
├── pytest.ini                   # Markers: smoke, regression, bug, gdpr, ai_augmented
├── .gitignore
├── AI_USAGE.md
├── requirements.txt
└── README.md
```

## Running individual tasks

`run_all_tests.py` (above) is the one-command path and what a grader should
use. The commands below are for running one task/scenario at a time during
development — they assume dependencies are already installed.

### Task 1 — UI Tests
```bash
# All BDD scenarios
pytest ui_tests/step_defs/ -v

# Single feature
pytest ui_tests/step_defs/test_home_page.py -v
pytest ui_tests/step_defs/test_careers.py -v
pytest ui_tests/step_defs/test_job_listings.py -v
pytest ui_tests/step_defs/test_apply_flow.py -v

# By marker (smoke / regression / bug / gdpr)
pytest ui_tests/step_defs/ -m smoke -v
pytest ui_tests/step_defs/ -m "smoke and not bug" -v
pytest ui_tests/step_defs/ -m bug -v

# Single scenario (name match)
pytest ui_tests/step_defs/ -k "title" -v

# Headed mode (visible browser)
pytest ui_tests/step_defs/ -v --headed
```

### Task 2 — Load Test (n11.com search, 1 user, 60 seconds)
```bash
locust -f load_tests/locustfile.py --headless -u 1 -r 1 --run-time 60s --host https://www.n11.com
```

### Task 3 — API Tests (petstore.swagger.io)
```bash
# All CRUD tests
pytest api_tests/ -v

# Single class (e.g. just DELETE scenarios)
pytest api_tests/test_petstore.py::TestDeletePet -v

# Single test
pytest api_tests/test_petstore.py::TestCreatePet::test_create_pet_positive -v
```

### All tests + HTML report
```bash
pytest ui_tests/step_defs/ api_tests/ -v --html=report.html --self-contained-html
```

## Test Scenarios

### Task 1 — UI Automation (BDD: ui_tests/features/ + ui_tests/pages/ + ui_tests/step_defs/)
| Feature | Scenarios | Bugs found while testing |
|---|---|---|
| `home_page.feature` | Title, H1, nav, CTAs, footer, cookie banner, language switcher (display, actual switch, persistence across navigation) | Login link stays in English on the French page while everything else (nav, careers link, page title) translates |
| `careers.feature` | "See all teams" → QA card → Lever navigation | — |
| `job_listings.feature` | Position/Location/Department validation on Lever QA listing | Position uses "QA" not "Quality Assurance"; Location is "ISTANBUL" not "Istanbul, Turkey"; 1 job listed in Berlin, not Istanbul |
| `apply_flow.feature` | Apply button → Lever application form fields | — |

Markers: `@smoke`, `@regression`, `@bug` (defects this suite found and pinned down — not a pre-existing checklist), `@gdpr`, `@ai_augmented` (Task 1's required AI-Augmented Sub-Scenario — see `prompts/04_language_switch.md`).

**AI-Augmented Sub-Scenario** (required by the assignment): the language
switcher originally only had a test that checked the dropdown *lists*
"English/Français/Español" — never that picking one actually does anything.
Added 3 scenarios across 2 prompt iterations: switching language actually
navigates to the localized page (`/fr/`, translated title); that locale
survives navigating to a *different* page (the careers link stays under
`/fr/careers/`); and a bug found while checking that — the login link is the
one piece of header chrome that doesn't translate. Full investigation and
iteration log in `prompts/04_language_switch.md`.

### Task 2 — Load Test Scenarios
1 user is used throughout (sufficient per the assignment); the test is built
to find a real regression, not just confirm `200 OK`. Each request asserts
both a response-time SLA (`RESPONSE_TIME_SLA_MS = 2000`) and the actual page
structure (`totalCount` field, `product-item` tiles, `empty-search-result`
marker), not a substring match.

| Task | Scenario |
|---|---|
| ASCII search terms | GET /arama?q={laptop,telefon,kitap} — asserts totalCount > 0 and product tiles render |
| Turkish-character terms | GET /arama?q={kulaklık,çanta,şapka} — same assertions, isolated to catch encoding-specific regressions |
| No-results term | GET /arama?q=zzxxqqnonexistent123 — asserts the empty-state marker, not just status 200 |
| Empty query | GET /arama?q= — site redirects to the homepage; asserted as a documented behavior |
| Long query (boundary) | GET /arama?q={300 chars} — asserts no 5xx |

**Bug found:** ~10-20% of requests across all of the above (not tied to a
specific term or character set) hit a 2-3.5s latency spike against a normal
110-200ms response time — a 15-20x jump with no client-side explanation.
The SLA assertion turns this into a deterministic, repeatable failure
instead of a one-off observation buried in a percentile chart. See
`prompts/02_load_test.md` for the investigation (including a Cloudflare
403 on `curl` and on Locust's default User-Agent, both worked around).

### Task 3 — API Tests
| Class | Scenarios | Bugs found while testing |
|---|---|---|
| `TestCreatePet` | Positive create, response schema, missing `photoUrls`, invalid JSON, negative ID, invalid status enum, unicode name, empty name, duplicate-ID upsert | Negative ID (`-1`) silently overflows to int64 max (`9223372036854775807`); invalid `status` enum values accepted instead of rejected with 400 |
| `TestReadPet` | Get by ID, 404, invalid ID format, zero ID, response time, findByStatus (single/multi/invalid), findByTags, content-type | — |
| `TestUpdatePet` | Positive update, upsert-on-unknown-ID, form-data update, invalid status enum, field-preservation on partial update | Same status-enum validation gap as create |
| `TestDeletePet` | Positive delete, 404 on missing ID, invalid ID format, post-delete unreachability, double-delete idempotency, delete with `api_key` header | DELETE on a non-existent pet ID returns 200 instead of 404 |

Uses `PetstoreClient` (`api_tests/clients/petstore_client.py`) as a thin HTTP
wrapper — the API equivalent of the UI Page Object Model. The Petstore
sandbox is a shared public demo backend, so tests use randomized IDs
(`unique_id` / `pet_factory` fixtures) to avoid collisions with other
test runs, and the `pet_factory` fixture guarantees cleanup even on failure.

## Notes on AI Usage
See "How This Was Built" above for the collaboration pattern, `AI_USAGE.md`
for answers to the four required questions, and `prompts/` for the prompt
iteration logs (Task 1's AI-generated scenario, and Task 2's load-test
redesign — `prompts/02_load_test.md` is the AI-assisted investigation that
led to the bug reported above).
