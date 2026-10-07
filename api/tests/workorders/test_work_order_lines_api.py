"""Tests for the work-order quote-lines HTTP API
(/api/work-orders/{id}/lines).

Defects these catch:
- a line add posts stock prematurely, or the order's total omits a line
  kind;
- an inventory-part line accepts a cross-tenant or made-up item id, or an
  archived item;
- a retry of `POST .../lines` with the same id and payload duplicates the
  line, or a conflicting replay silently overwrites the original;
- editing or removing a line id that doesn't exist on the order (or
  belongs to another order) is accepted instead of rejected;
- removing a line twice (idempotent soft removal) removes it "more", or
  a removed line is still counted in the total.
"""

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

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


def _active_vehicle(client: TestClient) -> dict:
    customer = _create_customer(client)
    return _create_vehicle(client, customer_id=customer["id"])


def _create_order(client: TestClient, *, vehicle_id: str, **overrides: object) -> dict:
    payload = {"id": str(uuid.uuid4()), "vehicle_id": vehicle_id}
    payload.update(overrides)
    response = client.post("/api/work-orders", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_item(client: TestClient, **overrides: object) -> dict:
    payload = {"name": "Filtro de aceite", "category": "Filtros", "unit": "unidad"}
    payload.update(overrides)
    response = client.post("/api/inventory/items", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _labor_line(**overrides: object) -> dict:
    payload = {
        "id": str(uuid.uuid4()),
        "kind": "labor",
        "description": "Cambio de aceite",
        "quantity": 1,
        "unit_price_cents": 15000,
    }
    payload.update(overrides)
    return payload


def _part_line(*, item_id: str, **overrides: object) -> dict:
    payload = {
        "id": str(uuid.uuid4()),
        "kind": "inventory_part",
        "item_id": item_id,
        "description": "Filtro de aceite",
        "quantity": 1,
        "unit_price_cents": 8000,
    }
    payload.update(overrides)
    return payload


def _external_line(**overrides: object) -> dict:
    payload = {
        "id": str(uuid.uuid4()),
        "kind": "external_part",
        "description": "Llanta nueva",
        "quantity": 1,
        "unit_price_cents": 90000,
    }
    payload.update(overrides)
    return payload


def test_adding_each_line_kind_builds_the_total_without_posting_stock(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    item = _create_item(authenticated_client, initial_stock=10)

    labor = _labor_line(quantity=1, unit_price_cents=15000)
    part = _part_line(item_id=item["id"], quantity=2, unit_price_cents=8000)
    external = _external_line(quantity=1, unit_price_cents=90000)

    for line in (labor, part, external):
        response = authenticated_client.post(f"/api/work-orders/{order['id']}/lines", json=line)
        assert response.status_code == 201, response.text

    final = authenticated_client.get(f"/api/work-orders/{order['id']}").json()
    assert final["total_cents"] == 15000 + 2 * 8000 + 90000
    assert len(final["lines"]) == 3

    item_after = authenticated_client.get(f"/api/inventory/items/{item['id']}").json()
    assert item_after["stock"] == 10  # unchanged: no movement posted by adding lines


def test_part_line_with_a_nonexistent_item_id_is_not_found(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])

    response = authenticated_client.post(
        f"/api/work-orders/{order['id']}/lines",
        json=_part_line(item_id=str(uuid.uuid4())),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "item_not_found"
    assert authenticated_client.get(f"/api/work-orders/{order['id']}").json()["lines"] == []


def test_part_line_with_a_foreign_item_id_is_not_found(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    foreign_item = _create_item(second_authenticated_client)

    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])

    response = authenticated_client.post(
        f"/api/work-orders/{order['id']}/lines",
        json=_part_line(item_id=foreign_item["id"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "item_not_found"


def test_part_line_with_an_archived_item_is_not_found(authenticated_client: TestClient) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    item = _create_item(authenticated_client)
    archive_response = authenticated_client.post(f"/api/inventory/items/{item['id']}/archive")
    assert archive_response.status_code == 204

    response = authenticated_client.post(
        f"/api/work-orders/{order['id']}/lines", json=_part_line(item_id=item["id"])
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "item_not_found"


def test_replaying_an_identical_line_add_is_a_no_op(authenticated_client: TestClient) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    line = _labor_line()
    first = authenticated_client.post(f"/api/work-orders/{order['id']}/lines", json=line)
    assert first.status_code == 201

    replay = authenticated_client.post(f"/api/work-orders/{order['id']}/lines", json=line)

    assert replay.status_code == 200
    assert len(replay.json()["lines"]) == 1


def test_reusing_a_line_id_with_a_different_payload_is_a_conflict(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    line = _labor_line(quantity=1)
    authenticated_client.post(f"/api/work-orders/{order['id']}/lines", json=line)

    conflicting = dict(line, quantity=2)
    response = authenticated_client.post(f"/api/work-orders/{order['id']}/lines", json=conflicting)

    assert response.status_code == 409
    assert response.json()["detail"] == "work_order_line_id_conflict"
    unchanged = authenticated_client.get(f"/api/work-orders/{order['id']}").json()
    assert unchanged["lines"][0]["quantity"] == 1


def test_editing_a_nonexistent_line_is_not_found(authenticated_client: TestClient) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])

    response = authenticated_client.patch(
        f"/api/work-orders/{order['id']}/lines/{uuid.uuid4()}", json={"quantity": 2}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "work_order_line_not_found"


def test_editing_a_line_belonging_to_another_order_is_not_found(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order_one = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    order_two = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    line = _labor_line()
    authenticated_client.post(f"/api/work-orders/{order_one['id']}/lines", json=line)

    response = authenticated_client.patch(
        f"/api/work-orders/{order_two['id']}/lines/{line['id']}", json={"quantity": 2}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "work_order_line_not_found"


def test_editing_a_lines_quantity_and_price_updates_the_total(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    line = _labor_line(quantity=1, unit_price_cents=10000)
    authenticated_client.post(f"/api/work-orders/{order['id']}/lines", json=line)

    response = authenticated_client.patch(
        f"/api/work-orders/{order['id']}/lines/{line['id']}", json={"quantity": 3}
    )

    assert response.status_code == 200
    assert response.json()["total_cents"] == 3 * 10000


def test_removing_a_nonexistent_line_is_not_found(authenticated_client: TestClient) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])

    response = authenticated_client.delete(f"/api/work-orders/{order['id']}/lines/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "work_order_line_not_found"


def test_removing_a_line_excludes_it_from_the_order(authenticated_client: TestClient) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    line = _labor_line(unit_price_cents=10000)
    authenticated_client.post(f"/api/work-orders/{order['id']}/lines", json=line)

    response = authenticated_client.delete(f"/api/work-orders/{order['id']}/lines/{line['id']}")

    assert response.status_code == 200
    assert response.json()["lines"] == []
    assert response.json()["total_cents"] == 0


def test_removing_a_line_twice_is_idempotent(authenticated_client: TestClient) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    line = _labor_line()
    authenticated_client.post(f"/api/work-orders/{order['id']}/lines", json=line)
    authenticated_client.delete(f"/api/work-orders/{order['id']}/lines/{line['id']}")

    second = authenticated_client.delete(f"/api/work-orders/{order['id']}/lines/{line['id']}")

    assert second.status_code == 200
    assert second.json()["lines"] == []
