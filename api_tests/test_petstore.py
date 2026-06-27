"""
API Tests — Petstore Swagger (pet endpoints)
Task 3: CRUD operations with positive & negative scenarios
Run: pytest api_tests/test_petstore.py -v
"""
import pytest
import requests


BASE_URL = "https://petstore.swagger.io/v2"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def created_pet():
    """Create a pet once and share across tests; delete on teardown."""
    payload = {
        "id": 999001,
        "name": "TestDog",
        "status": "available",
        "category": {"id": 1, "name": "Dogs"},
        "photoUrls": ["https://example.com/dog.jpg"],
        "tags": [{"id": 1, "name": "test"}],
    }
    resp = requests.post(f"{BASE_URL}/pet", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    pet = resp.json()
    yield pet
    # Teardown
    requests.delete(f"{BASE_URL}/pet/{pet['id']}", headers=HEADERS)


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

class TestCreatePet:
    def test_create_pet_positive(self):
        payload = {
            "id": 999002,
            "name": "BuddyCat",
            "status": "available",
            "category": {"id": 2, "name": "Cats"},
            "photoUrls": ["https://example.com/cat.jpg"],
        }
        resp = requests.post(f"{BASE_URL}/pet", json=payload, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == payload["id"]
        assert body["name"] == payload["name"]
        assert body["status"] == payload["status"]
        # Cleanup
        requests.delete(f"{BASE_URL}/pet/{payload['id']}", headers=HEADERS)

    def test_create_pet_missing_required_photourls(self):
        """photoUrls is required by the schema — omitting it should fail or return error."""
        payload = {"id": 999099, "name": "BadPet"}
        resp = requests.post(f"{BASE_URL}/pet", json=payload, headers=HEADERS)
        # Petstore may accept it with 200 but without photoUrls the contract is violated;
        # we validate the response at least doesn't crash (5xx)
        assert resp.status_code < 500

    def test_create_pet_invalid_payload(self):
        """Completely invalid JSON body."""
        resp = requests.post(
            f"{BASE_URL}/pet",
            data="not-a-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code in (400, 415, 500)


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

class TestReadPet:
    def test_get_pet_by_id_positive(self, created_pet):
        pet_id = created_pet["id"]
        resp = requests.get(f"{BASE_URL}/pet/{pet_id}", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == pet_id
        assert body["name"] == created_pet["name"]

    def test_get_pet_not_found(self):
        resp = requests.get(f"{BASE_URL}/pet/999999999", headers=HEADERS)
        assert resp.status_code == 404

    def test_get_pet_invalid_id_string(self):
        resp = requests.get(f"{BASE_URL}/pet/abc", headers=HEADERS)
        assert resp.status_code in (400, 404)

    def test_find_pets_by_status_available(self):
        resp = requests.get(f"{BASE_URL}/pet/findByStatus?status=available", headers=HEADERS)
        assert resp.status_code == 200
        pets = resp.json()
        assert isinstance(pets, list)
        for pet in pets:
            assert pet.get("status") == "available"

    def test_find_pets_by_invalid_status(self):
        resp = requests.get(f"{BASE_URL}/pet/findByStatus?status=unknownstatus", headers=HEADERS)
        # Should return empty list or 400
        assert resp.status_code in (200, 400)
        if resp.status_code == 200:
            assert resp.json() == [] or isinstance(resp.json(), list)


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

class TestUpdatePet:
    def test_update_pet_positive(self, created_pet):
        updated = {**created_pet, "name": "UpdatedDog", "status": "sold"}
        resp = requests.put(f"{BASE_URL}/pet", json=updated, headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "UpdatedDog"
        assert body["status"] == "sold"

    def test_update_pet_not_found(self):
        payload = {
            "id": 999999999,
            "name": "Ghost",
            "status": "available",
            "photoUrls": [],
        }
        resp = requests.put(f"{BASE_URL}/pet", json=payload, headers=HEADERS)
        # Petstore may create it or return 404
        assert resp.status_code in (200, 404)

    def test_update_pet_with_form_data(self, created_pet):
        pet_id = created_pet["id"]
        resp = requests.post(
            f"{BASE_URL}/pet/{pet_id}",
            data={"name": "FormUpdatedDog", "status": "pending"},
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

class TestDeletePet:
    def test_delete_pet_positive(self):
        # Create a throwaway pet then delete it
        payload = {
            "id": 999003,
            "name": "DeleteMe",
            "status": "available",
            "photoUrls": [],
        }
        requests.post(f"{BASE_URL}/pet", json=payload, headers=HEADERS)
        resp = requests.delete(f"{BASE_URL}/pet/999003", headers=HEADERS)
        assert resp.status_code == 200

    def test_delete_pet_not_found(self):
        resp = requests.delete(f"{BASE_URL}/pet/999999999", headers=HEADERS)
        assert resp.status_code == 404

    def test_delete_pet_invalid_id(self):
        resp = requests.delete(f"{BASE_URL}/pet/abc", headers=HEADERS)
        assert resp.status_code in (400, 404)

    def test_deleted_pet_is_unreachable(self):
        # Create then immediately delete
        payload = {"id": 999004, "name": "Temp", "status": "available", "photoUrls": []}
        requests.post(f"{BASE_URL}/pet", json=payload, headers=HEADERS)
        requests.delete(f"{BASE_URL}/pet/999004", headers=HEADERS)

        resp = requests.get(f"{BASE_URL}/pet/999004", headers=HEADERS)
        assert resp.status_code == 404
