# AI Usage Documentation

## 1. Context, Prompt, Skill, Agent — in relation to AI coding assistants

**Context** is the information you supply to the AI before or alongside your request — existing code, file structure, constraints, or examples that shape what the AI produces. Without context, the AI works from generic knowledge; with context, it can generate code that fits your specific codebase.

**Prompt** is the natural-language instruction you send to the AI — the actual question or command that drives the response. A well-structured prompt is specific about the goal, the constraints, and the expected format of the output.

**Skill** refers to a reusable, pre-defined capability that an AI assistant can invoke — such as "write a Playwright test" or "generate a load test" — often packaged as a template or tool within the assistant's system. Skills encode best practices so you don't have to re-explain them every time.

**Agent** is an AI system that can autonomously plan and execute multi-step tasks, calling tools (file read/write, web search, code execution) and making decisions along the way, rather than just responding to a single prompt.

## 2. How I validated the AI output — what I rejected and why

I didn't validate by reading the code — I validated by actually running every suite against the live sites, repeatedly, and treating any unexpected result as something to dig into rather than accept. Two concrete examples from this project:

- An early fix for the careers-page cookie banner clicked the real "Accept All" button to get it out of the way. That silently set a real consent cookie on the shared browser session, which broke an *unrelated* test later in the same run (the home page's "fresh visit shows the cookie banner" check) — only caught by re-running the full suite and noticing a test that had nothing to do with my change start failing.
- The load test's first explanation for slow search responses was "Turkish-character query terms are slower to process." I rejected that explanation specifically — not the code, the *story* — because running the test a few more times showed the slowness was random and hit ASCII terms just as often. The fix was the same SLA assertion either way; the writeup had to be rewritten to match the data instead of the first plausible guess.
- For Task 1's required AI-Augmented Sub-Scenario (the language switcher, see `prompts/04_language_switch.md`), the AI's first draft reused an existing locator (`.first`, no visibility check) to click a locale option. I rejected it even though it passed locally — it happened to work but wasn't safe, since that locator matches both a desktop and a hidden mobile-nav duplicate, and `.first` isn't guaranteed to resolve to the visible one. I had it add a separate locator that filters for `is_visible()` instead of changing the original, which an unrelated existing test still depended on.

## 3. One point where AI was weak — and how I solved it manually

The AI's own testing of the load test only ever ran it from a plain terminal, where it always finished cleanly. I ran it the way the project is actually meant to be used — through VS Code's Run & Debug panel — and it hung indefinitely, twice, for two different reasons (once a missing request timeout, once a real Locust/`gevent` vs. `debugpy` incompatibility with no error message at all). The AI had no way to know that gap existed until I reported the exact symptom (process alive, near-zero CPU, no open network connection) from the actual hung process. That's a pattern I'd watch for generally: an AI assistant will confidently say a thing "works" based on how *it* tested it, which isn't necessarily how the thing will actually be used.

A smaller version of the same gap showed up in the Task 1 sub-scenario: the AI's "language switch actually works" investigation stopped at the current page, so it missed that the switch needed to be checked again after navigating *away* — I had to ask for that explicitly before the persistence scenario, and the login-link bug, ever got found.

## 4. When I would prefer to write code manually instead of using AI

I prefer writing manually when the bug is more about *judgment* than code — deciding whether a failing assertion is a real product defect worth documenting or just a flaky test, for instance. That call has to come from someone making a decision and standing behind it, not from a tool generating a plausible-sounding fix. I also write short one-off assertions by hand when explaining the context would take longer than just writing the line.
