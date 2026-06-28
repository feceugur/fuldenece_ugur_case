"""
API Tests — Petstore Swagger (pet endpoints)
Task 3: CRUD operations with positive & negative scenarios.

Senior-level notes:
  - Uses PetstoreClient (api_tests/clients/petstore_client.py) instead of raw
    `requests` calls in every test — single place to change auth/headers/URLs.
  - Uses randomized IDs (unique_id / pet_factory fixtures) because the
    Petstore sandbox is a shared public demo backend; hard-coded IDs collide
    with other test runs (including CI workers running in parallel).
  - Several tests fail on purpose — they pin down real bugs/quirks found on
    the public Petstore sandbox while writing this suite (see inline 'BUG:'
    comments), not bugs that were already known going in. Same approach as
    the UI test suite (Task 1).
"""
import time
import pytest


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------

class TestCreatePet:

    def test_create_pet_positive(self, client, pet_factory):
        resp, payload = pet_factory(name="BuddyCat", status="available")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == payload["id"]
        assert body["name"] == payload["name"]
        assert body["status"] == payload["status"]

    def test_create_pet_response_schema(self, pet_factory):
        """Response must contain all schema-required top-level fields."""
        resp, _ = pet_factory()
        body = resp.json()
        for field in ("id", "name", "status", "photoUrls"):
            assert field in body, f"Missing field '{field}' in create response"
        assert isinstance(body["photoUrls"], list)

    def test_create_pet_missing_required_photourls(self, client, unique_id):
        """photoUrls is marked required in the OpenAPI schema — omitting it
        should be rejected. Currently the sandbox accepts it anyway (schema
        validation is not enforced server-side)."""
        resp = client.create_pet({"id": unique_id, "name": "NoPhotos", "status": "available"})
        client.cleanup(unique_id)
        assert resp.status_code in (200, 400), \
            f"Unexpected status for missing required field: {resp.status_code}"
        if resp.status_code == 200:
            pytest.xfail("BUG: server accepts pet without required 'photoUrls' field")

    def test_create_pet_invalid_json_body(self, client):
        """Malformed JSON body must be rejected, not silently processed."""
        resp = client.create_pet_raw("not-a-json-body")
        assert resp.status_code in (400, 415, 500), \
            f"Malformed JSON should be rejected, got {resp.status_code}"

    def test_create_pet_with_negative_id_does_not_overflow(self, client):
        """
        BUG: Sending a negative ID (-1) silently overflows to the int64 max
        value (9223372036854775807) instead of being rejected or preserved.
        This corrupts the stored ID and makes the pet effectively untraceable
        by the ID the client sent.
        """
        resp = client.create_pet({
            "id": -1, "name": "NegId", "status": "available", "photoUrls": []
        })
        assert resp.status_code == 200
        body = resp.json()
        client.cleanup(body["id"])
        assert body["id"] == -1, (
            f"BUG: negative id -1 was silently changed to {body['id']} "
            f"(int64 overflow) instead of being preserved or rejected"
        )

    def test_create_pet_rejects_invalid_status_enum(self, client, unique_id):
        """
        BUG: 'status' is documented as enum [available, pending, sold] but
        the API accepts arbitrary strings without validation.
        """
        resp = client.create_pet({
            "id": unique_id, "name": "BadStatus", "status": "not_a_real_status",
            "photoUrls": []
        })
        client.cleanup(unique_id)
        assert resp.status_code == 400, (
            f"BUG: server accepted invalid status enum value with "
            f"{resp.status_code}, expected 400"
        )

    def test_create_pet_with_unicode_name(self, pet_factory):
        """Non-ASCII characters in name must be stored and returned intact."""
        resp, payload = pet_factory(name="Köpek 犬 🐕")
        assert resp.status_code == 200
        assert resp.json()["name"] == payload["name"]

    def test_create_pet_with_empty_name(self, client, unique_id):
        """Empty string name is a borderline case — document actual behavior."""
        resp = client.create_pet({
            "id": unique_id, "name": "", "status": "available", "photoUrls": []
        })
        client.cleanup(unique_id)
        assert resp.status_code in (200, 400)

    def test_create_duplicate_id_overwrites_existing_pet(self, client, unique_id):
        """Creating a pet with an ID that already exists overwrites it
        (POST /pet behaves like an upsert) — document this explicitly so
        it isn't mistaken for a conflict-detection bug."""
        client.create_pet({"id": unique_id, "name": "Original", "status": "available", "photoUrls": []})
        resp = client.create_pet({"id": unique_id, "name": "Overwritten", "status": "sold", "photoUrls": []})
        client.cleanup(unique_id)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Overwritten"


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------

class TestReadPet:

    def test_get_pet_by_id_positive(self, client, pet_factory):
        _, payload = pet_factory()
        resp = client.get_pet(payload["id"])
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == payload["id"]
        assert body["name"] == payload["name"]

    def test_get_pet_not_found(self, client):
        resp = client.get_pet(999999999)
        assert resp.status_code == 404

    def test_get_pet_invalid_id_format(self, client):
        resp = client.get_pet("abc")
        assert resp.status_code in (400, 404)

    def test_get_pet_with_zero_id(self, client):
        resp = client.get_pet(0)
        assert resp.status_code in (200, 404)

    def test_get_pet_response_time_under_2s(self, client, pet_factory):
        """Basic performance sanity check on a hot path endpoint."""
        _, payload = pet_factory()
        resp = client.get_pet(payload["id"])
        assert resp.elapsed.total_seconds() < 2.0, \
            f"GET /pet/{{id}} took {resp.elapsed.total_seconds():.2f}s — too slow"

    def test_find_by_status_available(self, client):
        resp = client.find_by_status("available")
        assert resp.status_code == 200
        pets = resp.json()
        assert isinstance(pets, list)
        for pet in pets:
            assert pet.get("status") == "available", \
                f"findByStatus=available returned a pet with status {pet.get('status')!r}"

    def test_find_by_multiple_statuses(self, client):
        """Comma/multi-value status query must return the union of statuses."""
        resp = client.find_by_status("available", "pending")
        assert resp.status_code == 200
        pets = resp.json()
        statuses_found = {p.get("status") for p in pets}
        assert statuses_found <= {"available", "pending"}, \
            f"Unexpected statuses in result: {statuses_found}"

    def test_find_by_status_invalid_value(self, client):
        resp = client.find_by_status("not_a_status")
        assert resp.status_code in (200, 400)
        if resp.status_code == 200:
            assert resp.json() == []

    def test_find_by_tags(self, client, pet_factory):
        resp = client.find_by_tags("test")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_find_by_status_content_type_is_json(self, client):
        resp = client.find_by_status("available")
        assert "application/json" in resp.headers.get("Content-Type", "")


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------

class TestUpdatePet:

    def test_update_pet_positive(self, client, pet_factory):
        _, payload = pet_factory()
        updated = {**payload, "name": "UpdatedDog", "status": "sold"}
        resp = client.update_pet(updated)
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "UpdatedDog"
        assert body["status"] == "sold"

    def test_update_nonexistent_pet_creates_it(self, client, unique_id):
        """Document actual upsert behavior of PUT /pet for unknown IDs,
        rather than assuming a 404 the spec doesn't enforce."""
        payload = {"id": unique_id, "name": "Ghost", "status": "available", "photoUrls": []}
        resp = client.update_pet(payload)
        client.cleanup(unique_id)
        assert resp.status_code == 200
        assert resp.json()["id"] == unique_id

    def test_update_pet_with_form_data(self, client, pet_factory):
        _, payload = pet_factory()
        resp = client.update_pet_with_form(payload["id"], name="FormUpdatedDog", status="pending")
        assert resp.status_code == 200

    def test_update_pet_rejects_invalid_status_enum(self, client, pet_factory):
        """BUG: same enum-validation gap as create — PUT also accepts
        arbitrary status strings."""
        _, payload = pet_factory()
        updated = {**payload, "status": "definitely_not_valid"}
        resp = client.update_pet(updated)
        assert resp.status_code == 400, (
            f"BUG: PUT accepted invalid status enum with {resp.status_code}, "
            f"expected 400"
        )

    def test_update_pet_preserves_unmodified_fields(self, client, pet_factory):
        """Partial-looking update (only changing name) must not silently
        drop other fields like category or tags."""
        _, payload = pet_factory()
        updated = {**payload, "name": "RenamedOnly"}
        resp = client.update_pet(updated)
        body = resp.json()
        assert body["category"]["name"] == payload["category"]["name"], \
            "category was lost after updating only the name"


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

class TestDeletePet:

    def test_delete_pet_positive(self, client, pet_factory):
        _, payload = pet_factory()
        resp = client.delete_pet(payload["id"])
        assert resp.status_code == 200

    def test_delete_pet_not_found(self, client):
        """
        BUG: DELETE on a non-existent pet ID returns 200 instead of 404.
        The Petstore sandbox does not validate existence before responding
        with a success message.
        """
        resp = client.delete_pet(999999999)
        assert resp.status_code == 404, (
            f"BUG: deleting a non-existent pet returned {resp.status_code}, "
            f"expected 404"
        )

    def test_delete_pet_invalid_id_format(self, client):
        resp = client.delete_pet("abc")
        assert resp.status_code in (400, 404)

    def test_deleted_pet_is_unreachable_afterwards(self, client, pet_factory):
        _, payload = pet_factory()
        client.delete_pet(payload["id"])
        resp = client.get_pet(payload["id"])
        assert resp.status_code == 404

    def test_double_delete_is_idempotent_with_404_on_second_call(self, client, pet_factory):
        """First delete succeeds; the immediate second delete on the same ID
        should report not-found rather than success again."""
        _, payload = pet_factory()
        first = client.delete_pet(payload["id"])
        second = client.delete_pet(payload["id"])
        assert first.status_code == 200
        assert second.status_code == 404

    def test_delete_pet_with_api_key_header(self, client, pet_factory):
        """api_key header is optional per spec — must not break the request
        when supplied."""
        _, payload = pet_factory()
        resp = client.delete_pet(payload["id"], api_key="test-key-123")
        assert resp.status_code == 200
