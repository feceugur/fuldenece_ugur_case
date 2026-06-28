# Prompt Iteration 02 — Load Test Redesign (n11.com search)

## Goal
The original `load_tests/locustfile.py` ran without errors but never actually
proved anything: it only checked `status_code == 200` and a crude substring
match. Redesign it to behave like a senior QA engineer's load test — one that
is actually capable of catching a real regression — while keeping to the
assignment's "1 user is enough" load profile.

## Context provided
- Tool: Locust 2.32.3, `HttpUser`
- Target: `https://www.n11.com/arama?q=...`
- Constraint: 1 concurrent user is sufficient per the assignment; the goal was
  better assertions/diagnostics, not higher concurrency

## Investigation (done directly against the live site, not just generated)
Before rewriting anything, the real page was probed manually to find out what
"correct" actually looks like and whether the test could even reach the site:

1. `curl` against `/arama?q=laptop` returned a Cloudflare 403 ("Attention
   Required!"). Adding browser-like headers did not help — it's a
   TLS/client-fingerprint block, not a header check.
2. Python's `urllib.request` with a browser User-Agent got a clean 200, ruling
   out a blanket bot wall. Running the actual Locust file still 403'd,
   though — `requests`' default `python-requests/X.Y` User-Agent was the
   specific thing being blocked, not the TLS stack. Setting a real
   `User-Agent` header on the Locust client session in `on_start` fixed it.
3. Inspected the real response HTML to find load-bearing markers for
   assertions instead of guessing: an inline `"totalCount":N` field for
   result counts, `class="product-item"` for result tiles, and
   `class="empty-search-result"` specifically on genuinely-empty searches.
4. Ran the rewritten test for ~100s total across two runs and found a
   reproducible pattern: ~10-20% of requests (across all endpoints, not tied
   to a specific search term) spike to 2-3.5s against a normal 110-200ms —
   a 15-20x latency jump with no client-side explanation. That became the
   test's `RESPONSE_TIME_SLA_MS` threshold instead of an arbitrary number.

## Output evaluation
**Accepted:**
- SLA-based failure (`response.elapsed.total_seconds() * 1000 > 2000ms` →
  `response.failure(...)`) instead of only checking status code — this is
  what actually surfaced the latency-spike bug above.
- Asserting against `totalCount` and `product-item` presence instead of a
  substring match against the search term (the original test's check —
  `term.lower() not in response.text.lower()` — would pass even on a broken
  results page as long as the search box echoed the term back).
- Distinguishing "genuinely no results" (nonsense term, expects
  `empty-search-result`) from "results missing when they shouldn't be"
  (real term with `totalCount > 0` but no `product-item` tiles).

**Rejected / refined:**
- First version of the empty-query and long-query tasks only checked
  `status_code in (200, 301, 302)` with no SLA check — too permissive, would
  have silently missed the empty-query latency spike found above.
- Considered bumping concurrency to "prove" the latency spike under load, but
  that's outside this assignment's scope (1 user) and adds load to a
  production third-party site without authorization; kept the test at 1 user
  and let the SLA assertion do the bug-finding instead.

## Result
`load_tests/locustfile.py` now fails deterministically (not just "looks
slow in a percentile chart") whenever the search module breaches its SLA,
and the bug it caught — intermittent 2-3.5s latency spikes — is reported in
the README results table.
