"""Tests for the vehicles HTTP API (/api/vehicles, /api/customers/{id}/vehicles).

Defects these catch:
- the owner reference is dropped or unchecked at creation;
- an archived, foreign, or nonexistent customer id is still accepted for a
  new vehicle link (AD-14);
- a vehicle can be reassigned to a different customer after creation;
- a retry of `POST /vehicles` with the same id and payload duplicates the
  vehicle, or a conflicting replay silently overwrites the original;
- plate normalization is skipped at the API boundary;
- the per-workshop active-plate uniqueness index is missing, not partial
  (so an archived vehicle's plate still blocks reuse), not workshop-scoped,
  or compares unnormalized plates;
- the uniqueness pre-check runs before replay detection, so a replayed
  plated vehicle hits `plate_taken` against itself (AD-14's ordering rule);
- a plate race is swallowed as every integrity error, hiding real bugs, or
  surfaces as an unhandled 500 instead of `plate_taken`;
- `archived_at` is re-stamped on a repeated vehicle archive;
- archiving a customer leaves its vehicles' plates orphaned (reserved
  forever) instead of cascading the archive and freeing them;
- the customer search ignores a vehicle's plate, or searches an archived
  vehicle's plate;
- a missing `workshop_id` filter leaks or mutates another workshop's data.
"""

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from taller.customers.adapters.repositories import SqlAlchemyVehicleRepository
from taller.main import app


@pytest.fixture
def second_authenticated_client(client: TestClient) -> Generator[TestClient]:
    """A second TestClient, authenticated as an independent second workshop.

    Mirrors `test_customers_api.second_authenticated_client`.
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


def _create_customer(client: TestClient, **overrides: object) -> dict:
    payload = {"full_name": "Maria Hernandez"}
    payload.update(overrides)
    response = client.post("/api/customers", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_vehicle(client: TestClient, *, customer_id: str, **overrides: object) -> dict:
    payload = {"customer_id": customer_id, "vehicle_type": "car", "make": "Toyota"}
    payload.update(overrides)
    response = client.post("/api/vehicles", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_saves_the_vehicle_with_its_owner(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client)

    vehicle = _create_vehicle(authenticated_client, customer_id=customer["id"], make="Honda")

    assert vehicle["customer_id"] == customer["id"]
    assert vehicle["make"] == "Honda"


def test_create_with_a_nonexistent_customer_id_is_not_found(
    authenticated_client: TestClient,
) -> None:
    response = authenticated_client.post(
        "/api/vehicles",
        json={"customer_id": str(uuid.uuid4()), "vehicle_type": "car", "make": "Toyota"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "customer_not_found"


def test_create_with_a_foreign_customer_id_is_not_found(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    customer = _create_customer(authenticated_client)

    response = second_authenticated_client.post(
        "/api/vehicles",
        json={"customer_id": customer["id"], "vehicle_type": "car", "make": "Toyota"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "customer_not_found"


def test_create_with_an_archived_customer_id_is_not_found(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client)
    archive_response = authenticated_client.post(f"/api/customers/{customer['id']}/archive")
    assert archive_response.status_code == 204

    response = authenticated_client.post(
        "/api/vehicles",
        json={"customer_id": customer["id"], "vehicle_type": "car", "make": "Toyota"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "customer_not_found"


def test_an_edit_cannot_reassign_the_vehicle_to_a_different_customer(
    authenticated_client: TestClient,
) -> None:
    owner = _create_customer(authenticated_client, full_name="Owner")
    other = _create_customer(authenticated_client, full_name="Other")
    vehicle = _create_vehicle(authenticated_client, customer_id=owner["id"])

    response = authenticated_client.patch(
        f"/api/vehicles/{vehicle['id']}", json={"customer_id": other["id"], "make": "Nissan"}
    )

    assert response.status_code == 200
    assert response.json()["customer_id"] == owner["id"]
    detail = authenticated_client.get(f"/api/vehicles/{vehicle['id']}").json()
    assert detail["customer_id"] == owner["id"]


def test_replaying_an_identical_create_is_a_no_op(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client)
    client_id = "11111111-1111-1111-1111-111111111111"
    payload = {"id": client_id, "customer_id": customer["id"], "vehicle_type": "car", "make": "Kia"}

    first = authenticated_client.post("/api/vehicles", json=payload)
    assert first.status_code == 201

    replay = authenticated_client.post("/api/vehicles", json=payload)
    assert replay.status_code == 200
    assert replay.json() == first.json()

    listing = authenticated_client.get(f"/api/customers/{customer['id']}/vehicles")
    assert len(listing.json()) == 1


def test_replaying_an_id_with_a_different_plate_is_a_conflict(
    authenticated_client: TestClient,
) -> None:
    customer = _create_customer(authenticated_client)
    client_id = "22222222-2222-2222-2222-222222222222"
    original = authenticated_client.post(
        "/api/vehicles",
        json={"id": client_id, "customer_id": customer["id"], "vehicle_type": "car", "make": "Kia"},
    )
    assert original.status_code == 201

    conflicting = authenticated_client.post(
        "/api/vehicles",
        json={
            "id": client_id,
            "customer_id": customer["id"],
            "vehicle_type": "car",
            "make": "Kia",
            "plate": "HAB1234",
        },
    )

    assert conflicting.status_code == 409
    assert conflicting.json()["detail"] == "vehicle_id_conflict"


def test_a_plate_is_normalized_on_save(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client)

    vehicle = _create_vehicle(authenticated_client, customer_id=customer["id"], plate="hab-1234")

    assert vehicle["plate"] == "HAB1234"


def test_an_invalid_plate_is_rejected(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client)

    response = authenticated_client.post(
        "/api/vehicles",
        json={
            "customer_id": customer["id"],
            "vehicle_type": "car",
            "make": "Kia",
            "plate": "HAB#1",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "invalid_plate"


def test_a_duplicate_active_plate_in_the_same_workshop_is_rejected(
    authenticated_client: TestClient,
) -> None:
    customer = _create_customer(authenticated_client)
    _create_vehicle(authenticated_client, customer_id=customer["id"], plate="HAB1234")

    response = authenticated_client.post(
        "/api/vehicles",
        json={
            "customer_id": customer["id"],
            "vehicle_type": "car",
            "make": "Kia",
            "plate": "HAB 1234",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "plate_taken"


def test_several_unplated_vehicles_are_always_allowed(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client)
    _create_vehicle(authenticated_client, customer_id=customer["id"])

    second = authenticated_client.post(
        "/api/vehicles",
        json={"customer_id": customer["id"], "vehicle_type": "motorcycle", "make": "Yamaha"},
    )

    assert second.status_code == 201


def test_archiving_a_vehicle_frees_its_plate_for_reuse(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client)
    vehicle = _create_vehicle(authenticated_client, customer_id=customer["id"], plate="HAB1234")
    archive_response = authenticated_client.post(f"/api/vehicles/{vehicle['id']}/archive")
    assert archive_response.status_code == 204

    reused = authenticated_client.post(
        "/api/vehicles",
        json={
            "customer_id": customer["id"],
            "vehicle_type": "car",
            "make": "Kia",
            "plate": "HAB1234",
        },
    )

    assert reused.status_code == 201


def test_a_plate_unique_to_one_workshop_does_not_block_another(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    customer_a = _create_customer(authenticated_client)
    _create_vehicle(authenticated_client, customer_id=customer_a["id"], plate="HAB1234")
    customer_b = _create_customer(second_authenticated_client, full_name="Cliente B")

    response = second_authenticated_client.post(
        "/api/vehicles",
        json={
            "customer_id": customer_b["id"],
            "vehicle_type": "car",
            "make": "Kia",
            "plate": "HAB1234",
        },
    )

    assert response.status_code == 201


def test_replaying_a_plated_vehicle_create_is_not_reported_as_plate_taken(
    authenticated_client: TestClient,
) -> None:
    customer = _create_customer(authenticated_client)
    client_id = "33333333-3333-3333-3333-333333333333"
    payload = {
        "id": client_id,
        "customer_id": customer["id"],
        "vehicle_type": "car",
        "make": "Kia",
        "plate": "HAB1234",
    }

    first = authenticated_client.post("/api/vehicles", json=payload)
    assert first.status_code == 201

    replay = authenticated_client.post("/api/vehicles", json=payload)

    assert replay.status_code == 200


def test_a_plate_race_surfaces_as_plate_taken_not_an_unhandled_error(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    customer = _create_customer(authenticated_client)
    _create_vehicle(authenticated_client, customer_id=customer["id"], plate="HAB1234")
    # A concurrent create committed the plate after our pre-check ran: the
    # pre-check sees no collision, so only the database's unique index
    # catches it.
    monkeypatch.setattr(SqlAlchemyVehicleRepository, "get_active_by_plate", lambda *a, **kw: None)

    response = authenticated_client.post(
        "/api/vehicles",
        json={
            "customer_id": customer["id"],
            "vehicle_type": "car",
            "make": "Kia",
            "plate": "HAB1234",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "plate_taken"


def test_an_unrelated_integrity_error_is_not_reported_as_plate_taken(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    customer = _create_customer(authenticated_client)
    original_add = SqlAlchemyVehicleRepository.add

    def add_with_a_bogus_customer_id(self: SqlAlchemyVehicleRepository, vehicle: object) -> None:
        vehicle.customer_id = uuid.uuid4()
        original_add(self, vehicle)

    monkeypatch.setattr(SqlAlchemyVehicleRepository, "add", add_with_a_bogus_customer_id)

    # TestClient re-raises unhandled server errors: reaching here means the
    # route let the error surface (a 500) instead of mislabeling it
    # `plate_taken`.
    with pytest.raises(IntegrityError, match="vehicles_customer_id_fkey"):
        authenticated_client.post(
            "/api/vehicles",
            json={"customer_id": customer["id"], "vehicle_type": "car", "make": "Kia"},
        )


def test_archiving_twice_keeps_the_first_archived_at(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client)
    vehicle = _create_vehicle(authenticated_client, customer_id=customer["id"])

    first_archive = authenticated_client.post(f"/api/vehicles/{vehicle['id']}/archive")
    assert first_archive.status_code == 204
    first_archived_at = authenticated_client.get(f"/api/vehicles/{vehicle['id']}").json()[
        "archived_at"
    ]

    second_archive = authenticated_client.post(f"/api/vehicles/{vehicle['id']}/archive")
    assert second_archive.status_code == 204
    second_archived_at = authenticated_client.get(f"/api/vehicles/{vehicle['id']}").json()[
        "archived_at"
    ]

    assert second_archived_at == first_archived_at


def test_archiving_a_customer_archives_its_active_vehicles_and_frees_their_plates(
    authenticated_client: TestClient,
) -> None:
    customer = _create_customer(authenticated_client)
    vehicle_a = _create_vehicle(authenticated_client, customer_id=customer["id"], plate="HAB1234")
    vehicle_b = _create_vehicle(authenticated_client, customer_id=customer["id"], make="Honda")

    archive_response = authenticated_client.post(f"/api/customers/{customer['id']}/archive")
    assert archive_response.status_code == 204

    detail_a = authenticated_client.get(f"/api/vehicles/{vehicle_a['id']}").json()
    detail_b = authenticated_client.get(f"/api/vehicles/{vehicle_b['id']}").json()
    customer_archived_at = authenticated_client.get(f"/api/customers/{customer['id']}").json()[
        "archived_at"
    ]
    assert detail_a["archived_at"] == customer_archived_at
    assert detail_b["archived_at"] == customer_archived_at

    new_owner = _create_customer(authenticated_client, full_name="New Owner")
    freed_plate = authenticated_client.post(
        "/api/vehicles",
        json={
            "customer_id": new_owner["id"],
            "vehicle_type": "car",
            "make": "Kia",
            "plate": "HAB1234",
        },
    )
    assert freed_plate.status_code == 201


def test_an_already_archived_vehicle_is_unaffected_by_the_customer_archive_cascade(
    authenticated_client: TestClient,
) -> None:
    customer = _create_customer(authenticated_client)
    vehicle = _create_vehicle(authenticated_client, customer_id=customer["id"])
    first_archive = authenticated_client.post(f"/api/vehicles/{vehicle['id']}/archive")
    assert first_archive.status_code == 204
    archived_at_before = authenticated_client.get(f"/api/vehicles/{vehicle['id']}").json()[
        "archived_at"
    ]

    customer_archive = authenticated_client.post(f"/api/customers/{customer['id']}/archive")
    assert customer_archive.status_code == 204

    archived_at_after = authenticated_client.get(f"/api/vehicles/{vehicle['id']}").json()[
        "archived_at"
    ]
    assert archived_at_after == archived_at_before


def test_customer_search_matches_a_full_normalized_plate(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client, full_name="Ana Castillo")
    _create_vehicle(authenticated_client, customer_id=customer["id"], plate="HAB1234")

    response = authenticated_client.get("/api/customers", params={"q": "hab1234"})

    assert [row["full_name"] for row in response.json()] == ["Ana Castillo"]


def test_customer_search_matches_a_partial_plate(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client, full_name="Ana Castillo")
    _create_vehicle(authenticated_client, customer_id=customer["id"], plate="HAB1234")

    response = authenticated_client.get("/api/customers", params={"q": "hab12"})

    assert [row["full_name"] for row in response.json()] == ["Ana Castillo"]


def test_customer_search_does_not_match_an_archived_vehicles_plate(
    authenticated_client: TestClient,
) -> None:
    customer = _create_customer(authenticated_client, full_name="Ana Castillo")
    vehicle = _create_vehicle(authenticated_client, customer_id=customer["id"], plate="HAB1234")
    archive_response = authenticated_client.post(f"/api/vehicles/{vehicle['id']}/archive")
    assert archive_response.status_code == 204

    response = authenticated_client.get("/api/customers", params={"q": "hab1234"})

    assert response.json() == []


def test_another_workshops_vehicle_is_invisible(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    customer = _create_customer(authenticated_client)
    vehicle = _create_vehicle(authenticated_client, customer_id=customer["id"])

    response = second_authenticated_client.get(f"/api/vehicles/{vehicle['id']}")

    assert response.status_code == 404
    assert response.json()["detail"] == "vehicle_not_found"


def test_another_workshops_vehicle_cannot_be_mutated(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    customer = _create_customer(authenticated_client)
    vehicle = _create_vehicle(authenticated_client, customer_id=customer["id"], make="Toyota")

    patch_response = second_authenticated_client.patch(
        f"/api/vehicles/{vehicle['id']}", json={"make": "Hijacked"}
    )
    archive_response = second_authenticated_client.post(f"/api/vehicles/{vehicle['id']}/archive")

    assert patch_response.status_code == 404
    assert patch_response.json()["detail"] == "vehicle_not_found"
    assert archive_response.status_code == 404
    assert archive_response.json()["detail"] == "vehicle_not_found"

    unaffected = authenticated_client.get(f"/api/vehicles/{vehicle['id']}")
    assert unaffected.json()["make"] == "Toyota"
    assert unaffected.json()["archived_at"] is None


def test_workshop_b_creating_a_vehicle_under_workshop_as_customer_is_not_found(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    customer = _create_customer(authenticated_client)

    response = second_authenticated_client.post(
        "/api/vehicles",
        json={"customer_id": customer["id"], "vehicle_type": "car", "make": "Toyota"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "customer_not_found"


def test_listing_a_customers_vehicles_without_include_archived_returns_only_active(
    authenticated_client: TestClient,
) -> None:
    customer = _create_customer(authenticated_client)
    active_one = _create_vehicle(authenticated_client, customer_id=customer["id"], make="Toyota")
    active_two = _create_vehicle(authenticated_client, customer_id=customer["id"], make="Honda")
    archived = _create_vehicle(authenticated_client, customer_id=customer["id"], make="Mazda")
    archive_response = authenticated_client.post(f"/api/vehicles/{archived['id']}/archive")
    assert archive_response.status_code == 204

    response = authenticated_client.get(f"/api/customers/{customer['id']}/vehicles")

    ids = {row["id"] for row in response.json()}
    assert ids == {active_one["id"], active_two["id"]}
