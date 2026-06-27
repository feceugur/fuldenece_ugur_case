"""
Load Test — n11.com search module
Task 2: Search header + list results
Run: locust -f load_tests/locustfile.py --headless -u 1 -r 1 --run-time 60s
"""
from locust import HttpUser, task, between


class N11SearchUser(HttpUser):
    host = "https://www.n11.com"
    wait_time = between(1, 3)

    SEARCH_TERMS = ["laptop", "telefon", "kulaklık", "çanta", "kitap"]
    _term_index = 0

    def on_start(self):
        """Load the homepage first to warm cookies / session."""
        self.client.get("/", name="Home Page")

    @task(3)
    def search_product(self):
        term = self.SEARCH_TERMS[N11SearchUser._term_index % len(self.SEARCH_TERMS)]
        N11SearchUser._term_index += 1
        with self.client.get(
            f"/arama?q={term}",
            name="Search Results",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                if term.lower() not in response.text.lower() and "ürün bulunamadı" not in response.text.lower():
                    response.failure(f"Search term '{term}' not reflected in response")
                else:
                    response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def search_with_special_chars(self):
        """Edge case: search with special/Turkish characters."""
        with self.client.get(
            "/arama?q=şapka",
            name="Search - Turkish Chars",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 301, 302):
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    @task(1)
    def search_empty_query(self):
        """Edge case: empty search query."""
        with self.client.get(
            "/arama?q=",
            name="Search - Empty Query",
            catch_response=True,
        ) as response:
            # n11 may redirect or show all products — both are acceptable
            if response.status_code in (200, 301, 302):
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
