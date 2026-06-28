import random
import pytest

from clients.petstore_client import PetstoreClient


@pytest.fixture(scope="session")
def client() -> PetstoreClient:
    return PetstoreClient()


@pytest.fixture
def unique_id() -> int:
    """Random high ID to avoid collisions with other parallel test runs
    against the shared, public Petstore sandbox."""
    return random.randint(900_000_000, 999_999_999)


@pytest.fixture
def pet_factory(client, unique_id):
    """Creates a pet and guarantees cleanup, even on test failure."""
    created_ids = []

    def _create(**overrides):
        payload = {
            "id": unique_id,
            "name": "TestPet",
            "status": "available",
            "category": {"id": 1, "name": "Dogs"},
            "photoUrls": ["https://example.com/pet.jpg"],
            "tags": [{"id": 1, "name": "test"}],
        }
        payload.update(overrides)
        resp = client.create_pet(payload)
        created_ids.append(payload["id"])
        return resp, payload

    yield _create
    client.cleanup(*created_ids)
