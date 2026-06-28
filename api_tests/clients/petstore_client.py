"""
Thin HTTP client wrapper around the Petstore 'pet' endpoints.
Keeps URL/header construction out of test bodies — same intent
as the Page Object Model used for the UI tests.
"""
import requests


class PetstoreClient:
    BASE_URL = "https://petstore.swagger.io/v2"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    # --- CREATE / UPDATE ---

    def create_pet(self, payload: dict) -> requests.Response:
        return self.session.post(f"{self.BASE_URL}/pet", json=payload)

    def create_pet_raw(self, raw_body: str, content_type: str = "application/json") -> requests.Response:
        return self.session.post(
            f"{self.BASE_URL}/pet", data=raw_body, headers={"Content-Type": content_type}
        )

    def update_pet(self, payload: dict) -> requests.Response:
        return self.session.put(f"{self.BASE_URL}/pet", json=payload)

    def update_pet_with_form(self, pet_id: int, name: str = None, status: str = None) -> requests.Response:
        data = {}
        if name is not None:
            data["name"] = name
        if status is not None:
            data["status"] = status
        # Session default Content-Type is application/json — override it so
        # `requests` sets the correct multipart/form-urlencoded header itself.
        return self.session.post(
            f"{self.BASE_URL}/pet/{pet_id}",
            data=data,
            headers={"Accept": "application/json", "Content-Type": ""},
        )

    # --- READ ---

    def get_pet(self, pet_id) -> requests.Response:
        return self.session.get(f"{self.BASE_URL}/pet/{pet_id}")

    def find_by_status(self, *statuses: str) -> requests.Response:
        return self.session.get(
            f"{self.BASE_URL}/pet/findByStatus", params={"status": list(statuses)}
        )

    def find_by_tags(self, *tags: str) -> requests.Response:
        return self.session.get(
            f"{self.BASE_URL}/pet/findByTags", params={"tags": list(tags)}
        )

    # --- DELETE ---

    def delete_pet(self, pet_id, api_key: str = None) -> requests.Response:
        headers = {"api_key": api_key} if api_key else {}
        return self.session.delete(f"{self.BASE_URL}/pet/{pet_id}", headers=headers)

    # --- Helpers ---

    def cleanup(self, *pet_ids):
        """Best-effort teardown — ignore failures, pets may already be gone."""
        for pet_id in pet_ids:
            try:
                self.delete_pet(pet_id)
            except requests.RequestException:
                pass
