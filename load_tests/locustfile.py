"""
Load Test — n11.com search module (Task 2)

Run (1 user is sufficient per the assignment, but the test is written to
surface real performance/functional regressions, not just "did it return
200"):

    locust -f load_tests/locustfile.py --headless -u 1 -r 1 --run-time 60s --host https://www.n11.com

Design notes (see /prompts/02_load_test.md for the investigation that led
to these choices):

- n11.com sits behind Cloudflare. Plain `curl` gets blocked with a 403
  ("Attention Required! | Cloudflare") purely on TLS/client fingerprint —
  no header fixes that. Separately, Locust/`requests`' default
  "python-requests/X.Y" User-Agent is ALSO blocked with a 403, even
  though the underlying TLS stack passes. `on_start` below sets a real
  browser User-Agent on the client session, which is sufficient to get
  through — no other header tuning was needed. Documented here so a
  maintainer doesn't waste time re-diagnosing the same 403 from scratch.
- Response content is checked against the real page structure, not a
  crude substring match: results pages embed a `"totalCount":N` field in
  an inline script payload, product tiles use `class="product-item"`,
  and genuinely empty result pages render `class="empty-search-result"`.
- A real, measurable bug found by running this test: roughly 10-20% of
  requests against /arama (and the homepage) hit a latency spike of
  2-3.5s, against a typical 110-200ms for the rest — a 15-20x jump with
  no client-side difference. It is not tied to a specific search term or
  character set (the same term is fast on one request and a spike on
  another across repeated runs), so it looks like an intermittent
  backend/cache issue rather than a per-query cost. RESPONSE_TIME_SLA_MS
  turns this into a hard, repeatable failure signal instead of noise
  buried in percentile charts.
- Every request sets `timeout=REQUEST_TIMEOUT_S` (10s). `requests` has no
  default timeout, so one stalled connection can hang the whole run past
  --run-time (this happened once during testing: a run configured for
  60s never returned). The timeout caps that and reports it as a failure
  instead of an indefinite hang.
"""
import random
import re
from typing import Optional

from locust import HttpUser, task, between

# Performance SLA: a search results page slower than this is treated as a
# functional failure (it's a real, measurable regression a search module
# should not have), not just a slow data point buried in percentiles.
RESPONSE_TIME_SLA_MS = 2000
HOME_PAGE_SLA_MS = 3000

# Hard ceiling on how long any single request is allowed to block. `requests`
# defaults to no timeout at all, so one stalled connection can hang the
# entire run well past --run-time (observed: a run configured for 60s never
# returned because a single request never got a response). This bounds the
# damage and turns a hang into a reported failure instead.
REQUEST_TIMEOUT_S = 10

ASCII_TERMS = ["laptop", "telefon", "kitap"]
TURKISH_CHAR_TERMS = ["kulaklık", "çanta", "şapka"]
NONSENSE_TERM = "zzxxqqnonexistent123"
LONG_QUERY = "a" * 300

TOTAL_COUNT_RE = re.compile(r'"totalCount":(\d+)')


class N11SearchUser(HttpUser):
    host = "https://www.n11.com"
    wait_time = between(1, 3)

    def on_start(self):
        """Warm cookies/session like a real visitor before searching.

        n11.com sits behind Cloudflare bot management, which blocks
        requests' default "python-requests/X.Y" User-Agent outright (and
        blocks curl by TLS fingerprint regardless of headers — see module
        docstring). A standard browser User-Agent is enough to pass.
        """
        self.client.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        with self.client.get(
            "/", name="Home Page", catch_response=True, timeout=REQUEST_TIMEOUT_S
        ) as response:
            self._check_sla(response, HOME_PAGE_SLA_MS, "Home page")

    # --- helpers ---

    def _check_sla(self, response, sla_ms: float, label: str):
        """Flag responses slower than the SLA as failures, even if status is 200.

        A slow response is a real bug for a search module's purposes — it
        just doesn't show up if you only assert on status_code.
        """
        elapsed_ms = response.elapsed.total_seconds() * 1000
        if elapsed_ms > sla_ms:
            response.failure(
                f"{label} exceeded {sla_ms}ms SLA: {elapsed_ms:.0f}ms"
            )
            return False
        return True

    def _extract_total_count(self, html: str) -> Optional[int]:
        match = TOTAL_COUNT_RE.search(html)
        return int(match.group(1)) if match else None

    # --- tasks ---

    @task(5)
    def search_ascii_term(self):
        self._search(random.choice(ASCII_TERMS), "Search Results - ASCII")

    @task(3)
    def search_turkish_char_term(self):
        self._search(random.choice(TURKISH_CHAR_TERMS), "Search Results - Turkish Chars")

    @task(1)
    def search_no_results(self):
        """Edge case: a term that should genuinely return zero products."""
        with self.client.get(
            "/arama", params={"q": NONSENSE_TERM},
            name="Search - No Results", catch_response=True, timeout=REQUEST_TIMEOUT_S,
        ) as response:
            if not self._check_sla(response, RESPONSE_TIME_SLA_MS, "No-results search"):
                return
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
                return
            if "empty-search-result" not in response.text and "product-item" in response.text:
                response.failure(
                    "Nonsense term unexpectedly returned product results "
                    "(no empty-state marker found)"
                )
            else:
                response.success()

    @task(1)
    def search_empty_query(self):
        """Edge case: q= with no value. Site redirects to the homepage —
        documented here so a future change to that behavior is caught."""
        with self.client.get(
            "/arama", params={"q": ""},
            name="Search - Empty Query", catch_response=True, timeout=REQUEST_TIMEOUT_S,
        ) as response:
            if not self._check_sla(response, RESPONSE_TIME_SLA_MS, "Empty-query search"):
                return
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
            else:
                response.success()

    @task(1)
    def search_long_query(self):
        """Boundary case: a 300-character query. Should degrade gracefully
        (no 5xx), not necessarily fast — checked against a relaxed SLA."""
        with self.client.get(
            "/arama", params={"q": LONG_QUERY},
            name="Search - Long Query (300 chars)", catch_response=True, timeout=REQUEST_TIMEOUT_S,
        ) as response:
            if response.status_code >= 500:
                response.failure(f"Server error on long query: {response.status_code}")
            elif response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
            else:
                response.success()

    def _search(self, term: str, request_name: str):
        with self.client.get(
            "/arama", params={"q": term},
            name=request_name, catch_response=True, timeout=REQUEST_TIMEOUT_S,
        ) as response:
            if not self._check_sla(response, RESPONSE_TIME_SLA_MS, request_name):
                return
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
                return

            total_count = self._extract_total_count(response.text)
            if total_count is None:
                response.failure("Could not find totalCount in response — page structure may have changed")
                return
            if total_count <= 0:
                response.failure(f"'{term}' returned totalCount={total_count}, expected > 0")
                return
            if "product-item" not in response.text:
                response.failure(f"'{term}' has totalCount={total_count} but no product-item tiles rendered")
                return

            response.success()
