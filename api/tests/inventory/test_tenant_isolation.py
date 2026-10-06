"""Tests that one workshop's inventory is fully invisible to another.

Defects these catch:
- a repository query that forgets the `workshop_id` filter on one of the
  read or write paths, letting any authenticated user reach another
  workshop's items or movements by guessing/observing a UUID;
- an endpoint that returns a different status (e.g. 403 or an empty body
  with 200) for another workshop's item instead of a plain 404, which
  would itself leak that the id exists.
"""

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from taller.main import app


@pytest.fixture
def second_authenticated_client(client: TestClient) -> Generator[TestClient]:
    """A second TestClient, authenticated as an independent second workshop.

    Depends on `client` so the app's `get_db` override (the shared,
    transactional `db_session`) is already active; this only adds a second
    cookie jar authenticated as a different tenant on the same app/session.
    """
    with TestClient(app) as second_client:
        response = second_client.post(
            "/api/auth/register",
            json={
                "workshop_name": "Taller Rival",
                "owner_name": "Otra Persona",
                "phone": "99001122",
                "password": "another-strong-password",
            },
        )
        assert response.status_code == 201
        yield second_client


def _create_item(client: TestClient, **overrides: object) -> dict:
    payload = {"name": "Disco de freno"}
    payload.update(overrides)
    response = client.post("/api/inventory/items", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_second_workshop_cannot_see_the_first_workshops_item_in_list_or_get(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    item = _create_item(authenticated_client)

    get_response = second_authenticated_client.get(f"/api/inventory/items/{item['id']}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "item_not_found"

    list_response = second_authenticated_client.get("/api/inventory/items")
    assert item["id"] not in [row["id"] for row in list_response.json()]


def test_second_workshop_cannot_patch_archive_or_read_history_of_first_workshops_item(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    item = _create_item(authenticated_client)

    patch_response = second_authenticated_client.patch(
        f"/api/inventory/items/{item['id']}", json={"name": "Hijacked"}
    )
    archive_response = second_authenticated_client.post(
        f"/api/inventory/items/{item['id']}/archive"
    )
    history_response = second_authenticated_client.get(
        f"/api/inventory/items/{item['id']}/movements"
    )

    assert patch_response.status_code == 404
    assert archive_response.status_code == 404
    assert history_response.status_code == 404

    unaffected = authenticated_client.get(f"/api/inventory/items/{item['id']}")
    assert unaffected.json()["name"] == item["name"]
    assert unaffected.json()["archived_at"] is None


def test_second_workshop_cannot_record_a_movement_on_first_workshops_item(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    item = _create_item(authenticated_client)

    response = second_authenticated_client.put(
        f"/api/inventory/movements/{uuid.uuid4()}",
        json={"item_id": item["id"], "kind": "in", "quantity": 5},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "item_not_found"

    unaffected = authenticated_client.get(f"/api/inventory/items/{item['id']}")
    assert unaffected.json()["stock"] == 0
