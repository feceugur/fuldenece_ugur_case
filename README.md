# InsiderOne QA Engineer Assessment

Three-part test project covering UI automation, load testing, and API testing.

## Project Structure

```
CaseStudy/
├── ui_tests/
│   ├── conftest.py          # Playwright browser/page fixtures
│   └── test_insiderone.py   # Tasks 1.1–1.4 + AI sub-scenario
├── load_tests/
│   └── locustfile.py        # Task 2 — n11.com search load test
├── api_tests/
│   └── test_petstore.py     # Task 3 — Petstore CRUD API tests
├── prompts/
│   └── 01_contact_form.md   # AI prompt iteration log
├── AI_USAGE.md
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Running the Tests

### Task 1 — UI Tests (insiderone.com)
```bash
pytest ui_tests/ -v
```

### Task 2 — Load Test (n11.com search, 1 user, 60 seconds)
```bash
locust -f load_tests/locustfile.py --headless -u 1 -r 1 --run-time 60s --host https://www.n11.com
```

### Task 3 — API Tests (petstore.swagger.io)
```bash
pytest api_tests/ -v
```

### All tests + HTML report
```bash
pytest ui_tests/ api_tests/ -v --html=report.html --self-contained-html
```

## Test Scenarios

### Task 1 — UI Automation
| Class | Scenario |
|---|---|
| `TestHomePage` | Home page opens, title present, nav/hero/footer visible |
| `TestCareersPage` | "See all teams" click → QA positions → jobs list |
| `TestJobListings` | All jobs: Position/Department = "Quality Assurance", Location = "Istanbul, Turkey" |
| `TestApplyButton` | Apply → Lever application form URL |
| `TestAIGeneratedScenario` | Contact/Demo form renders + empty-submit validation |

### Task 2 — Load Test Scenarios
| Task | Scenario |
|---|---|
| Search product | GET /arama?q={term} for 5 common search terms |
| Turkish characters | GET /arama?q=şapka (special char handling) |
| Empty query | GET /arama?q= (edge case) |

### Task 3 — API Tests
| Class | Scenarios |
|---|---|
| `TestCreatePet` | Create (positive), missing photoUrls, invalid payload |
| `TestReadPet` | Get by ID, 404, invalid ID string, findByStatus, invalid status |
| `TestUpdatePet` | Update (positive), not found, form-data update |
| `TestDeletePet` | Delete (positive), 404, invalid ID, deleted pet unreachable |

## Notes on AI Usage
See `AI_USAGE.md` for answers to the four required questions and `prompts/` for
the full prompt iteration log for the AI-generated test scenario.
