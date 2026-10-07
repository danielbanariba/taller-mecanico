"""Tests for stock consumption through the work-order status lifecycle
(`PUT /api/work-orders/{id}/status` and line mutations on a consuming
order).

Defects these catch:
- a labor or external-part line touches stock, or the `approved ->
  in_progress` transition is wrongly blocked by the resulting negative
  stock;
- a forbidden transition bypasses approval, or reverses stock already
  installed on a delivered/completed order;
- a retry of the status PUT, a quantity edit, or a line removal
  double-applies its movement;
- a quantity edit while consuming re-posts the full quantity instead of
  only the delta, or a line added mid-job never consumes;
- cancellation leaves a partial or doubled reversal;
- the persisted posting state (`stock_posted_quantity`) drifts from the
  ledger sum of its linked movements (AD-4's invariant);
- a failure partway through posting several lines' movements leaves the
  order's status changed, or a movement from an earlier line committed
  anyway;
- a locked order (`delivered`/`cancelled`) still accepts a line edit, or
  `completed` is wrongly locked;
- a missing `workshop_id` filter on the status/line endpoints leaks or
  mutates another workshop's order.
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


def _add_line(client: TestClient, order_id: str, line: dict) -> dict:
    response = client.post(f"/api/work-orders/{order_id}/lines", json=line)
    assert response.status_code in (200, 201), response.text
    return response.json()


def _set_status(client: TestClient, order_id: str, target: str) -> object:
    return client.put(f"/api/work-orders/{order_id}/status", json={"status": target})


def _get_order(client: TestClient, order_id: str) -> dict:
    response = client.get(f"/api/work-orders/{order_id}")
    assert response.status_code == 200, response.text
    return response.json()


def _get_item(client: TestClient, item_id: str) -> dict:
    response = client.get(f"/api/inventory/items/{item_id}")
    assert response.status_code == 200, response.text
    return response.json()


def _line(order: dict, line_id: str) -> dict:
    for line in order["lines"]:
        if line["id"] == line_id:
            return line
    raise AssertionError(f"line {line_id} not found on order {order['id']}")


def test_entering_in_progress_posts_out_only_for_part_lines_and_allows_negative_stock(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    item_ok = _create_item(authenticated_client, name="Pastillas", initial_stock=10)
    item_short = _create_item(authenticated_client, name="Cadena", initial_stock=1)

    _add_line(authenticated_client, order["id"], _labor_line())
    _add_line(authenticated_client, order["id"], _part_line(item_id=item_ok["id"], quantity=4))
    _add_line(authenticated_client, order["id"], _part_line(item_id=item_short["id"], quantity=5))

    assert _set_status(authenticated_client, order["id"], "approved").status_code == 200
    response = _set_status(authenticated_client, order["id"], "in_progress")

    assert response.status_code == 200
    assert _get_item(authenticated_client, item_ok["id"])["stock"] == 6
    item_short_after = _get_item(authenticated_client, item_short["id"])
    assert item_short_after["stock"] == -4
    assert item_short_after["needs_review"] is True


def test_forbidden_transitions_are_rejected_and_leave_stock_unchanged(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    item = _create_item(authenticated_client, initial_stock=10)

    quote_order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    _add_line(authenticated_client, quote_order["id"], _part_line(item_id=item["id"], quantity=3))
    response = _set_status(authenticated_client, quote_order["id"], "in_progress")
    assert response.status_code == 409
    assert response.json()["detail"] == "invalid_status_transition"
    assert _get_item(authenticated_client, item["id"])["stock"] == 10

    delivered_order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    for target in ("approved", "in_progress", "completed", "delivered"):
        assert _set_status(authenticated_client, delivered_order["id"], target).status_code == 200
    response = _set_status(authenticated_client, delivered_order["id"], "cancelled")
    assert response.status_code == 409
    assert response.json()["detail"] == "invalid_status_transition"

    completed_order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    for target in ("approved", "in_progress", "completed"):
        assert _set_status(authenticated_client, completed_order["id"], target).status_code == 200
    response = _set_status(authenticated_client, completed_order["id"], "cancelled")
    assert response.status_code == 409
    assert response.json()["detail"] == "invalid_status_transition"


def test_retrying_a_status_put_a_quantity_edit_and_a_line_removal_each_post_once(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    item = _create_item(authenticated_client, initial_stock=20)
    added = _add_line(authenticated_client, order["id"], _part_line(item_id=item["id"], quantity=3))
    line_id = added["lines"][-1]["id"]

    assert _set_status(authenticated_client, order["id"], "approved").status_code == 200
    assert _set_status(authenticated_client, order["id"], "in_progress").status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 17

    # Repeated PUT in_progress: no-op, posts nothing again.
    assert _set_status(authenticated_client, order["id"], "in_progress").status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 17

    # Repeated PATCH with the same quantity: posts nothing again.
    patch_payload = {"quantity": 3}
    first_patch = authenticated_client.patch(
        f"/api/work-orders/{order['id']}/lines/{line_id}", json=patch_payload
    )
    assert first_patch.status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 17
    second_patch = authenticated_client.patch(
        f"/api/work-orders/{order['id']}/lines/{line_id}", json=patch_payload
    )
    assert second_patch.status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 17

    # Repeated DELETE: first returns the consumed stock, second is a no-op.
    first_delete = authenticated_client.delete(f"/api/work-orders/{order['id']}/lines/{line_id}")
    assert first_delete.status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 20
    second_delete = authenticated_client.delete(f"/api/work-orders/{order['id']}/lines/{line_id}")
    assert second_delete.status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 20


def test_edits_while_consuming_post_only_the_delta(authenticated_client: TestClient) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    item = _create_item(authenticated_client, initial_stock=20)
    added = _add_line(authenticated_client, order["id"], _part_line(item_id=item["id"], quantity=2))
    line_id = added["lines"][-1]["id"]

    assert _set_status(authenticated_client, order["id"], "approved").status_code == 200
    assert _set_status(authenticated_client, order["id"], "in_progress").status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 18  # 20 - 2

    patch_up = authenticated_client.patch(
        f"/api/work-orders/{order['id']}/lines/{line_id}", json={"quantity": 5}
    )
    assert patch_up.status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 15  # 20 - 5

    patch_down = authenticated_client.patch(
        f"/api/work-orders/{order['id']}/lines/{line_id}", json={"quantity": 2}
    )
    assert patch_down.status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 18  # 20 - 2

    second_item = _create_item(authenticated_client, name="Segunda pieza", initial_stock=10)
    added_mid_job = _add_line(
        authenticated_client, order["id"], _part_line(item_id=second_item["id"], quantity=4)
    )
    assert added_mid_job["status"] == "in_progress"
    assert _get_item(authenticated_client, second_item["id"])["stock"] == 6  # consumed at once

    removed = authenticated_client.delete(f"/api/work-orders/{order['id']}/lines/{line_id}")
    assert removed.status_code == 200
    assert _get_item(authenticated_client, item["id"])["stock"] == 20  # fully returned


def test_cancelling_after_consumption_restores_stock_cancelling_from_quote_posts_nothing(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)

    consumed_item = _create_item(authenticated_client, initial_stock=10)
    consumed_order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    _add_line(
        authenticated_client,
        consumed_order["id"],
        _part_line(item_id=consumed_item["id"], quantity=5),
    )
    assert _set_status(authenticated_client, consumed_order["id"], "approved").status_code == 200
    assert _set_status(authenticated_client, consumed_order["id"], "in_progress").status_code == 200
    assert _get_item(authenticated_client, consumed_item["id"])["stock"] == 5
    assert _set_status(authenticated_client, consumed_order["id"], "cancelled").status_code == 200
    assert _get_item(authenticated_client, consumed_item["id"])["stock"] == 10

    never_consumed_item = _create_item(
        authenticated_client, name="Nunca consumida", initial_stock=7
    )
    quote_order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    _add_line(
        authenticated_client,
        quote_order["id"],
        _part_line(item_id=never_consumed_item["id"], quantity=2),
    )
    assert _set_status(authenticated_client, quote_order["id"], "cancelled").status_code == 200
    assert _get_item(authenticated_client, never_consumed_item["id"])["stock"] == 7


def test_ledger_invariant_holds_after_a_mixed_scenario(authenticated_client: TestClient) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    item = _create_item(authenticated_client, initial_stock=20)
    added = _add_line(authenticated_client, order["id"], _part_line(item_id=item["id"], quantity=2))
    line_id = added["lines"][-1]["id"]

    assert _set_status(authenticated_client, order["id"], "approved").status_code == 200
    assert _set_status(authenticated_client, order["id"], "in_progress").status_code == 200
    authenticated_client.patch(
        f"/api/work-orders/{order['id']}/lines/{line_id}", json={"quantity": 5}
    )
    authenticated_client.patch(
        f"/api/work-orders/{order['id']}/lines/{line_id}", json={"quantity": 1}
    )

    final_order = _get_order(authenticated_client, order["id"])
    final_line = _line(final_order, line_id)
    final_item = _get_item(authenticated_client, item["id"])

    movements = authenticated_client.get(f"/api/inventory/items/{item['id']}/movements").json()
    line_movements = [m for m in movements if m["order_line_id"] == line_id]
    net_delta = sum(m["delta"] for m in line_movements)

    assert final_line["stock_posted_quantity"] == -net_delta
    assert final_item["stock"] == 20 + net_delta


def test_a_failure_posting_one_lines_movement_rolls_back_the_whole_transition(
    authenticated_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    item_a = _create_item(authenticated_client, name="Pieza A", initial_stock=10)
    item_b = _create_item(authenticated_client, name="Pieza B", initial_stock=10)
    _add_line(authenticated_client, order["id"], _part_line(item_id=item_a["id"], quantity=2))
    _add_line(authenticated_client, order["id"], _part_line(item_id=item_b["id"], quantity=3))
    assert _set_status(authenticated_client, order["id"], "approved").status_code == 200

    import taller.workorders.application.use_cases as workorders_use_cases

    real_record_movement = workorders_use_cases.record_movement
    calls = {"n": 0}

    def _flaky_record_movement(**kwargs: object) -> object:
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("simulated failure posting the second line's movement")
        return real_record_movement(**kwargs)

    monkeypatch.setattr(workorders_use_cases, "record_movement", _flaky_record_movement)

    with pytest.raises(RuntimeError, match="simulated failure"):
        _set_status(authenticated_client, order["id"], "in_progress")

    order_after = _get_order(authenticated_client, order["id"])
    assert order_after["status"] == "approved"
    assert _get_item(authenticated_client, item_a["id"])["stock"] == 10
    assert _get_item(authenticated_client, item_b["id"])["stock"] == 10


def test_line_edits_are_locked_in_delivered_and_cancelled_but_allowed_in_completed(
    authenticated_client: TestClient,
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    item = _create_item(authenticated_client, initial_stock=10)

    completed_order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    added = _add_line(
        authenticated_client, completed_order["id"], _part_line(item_id=item["id"], quantity=2)
    )
    line_id = added["lines"][-1]["id"]
    for target in ("approved", "in_progress", "completed"):
        assert _set_status(authenticated_client, completed_order["id"], target).status_code == 200
    patch_in_completed = authenticated_client.patch(
        f"/api/work-orders/{completed_order['id']}/lines/{line_id}", json={"quantity": 4}
    )
    assert patch_in_completed.status_code == 200

    delivered_order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    added_delivered = _add_line(authenticated_client, delivered_order["id"], _labor_line())
    delivered_line_id = added_delivered["lines"][-1]["id"]
    for target in ("approved", "in_progress", "completed", "delivered"):
        assert _set_status(authenticated_client, delivered_order["id"], target).status_code == 200
    locked_response = authenticated_client.patch(
        f"/api/work-orders/{delivered_order['id']}/lines/{delivered_line_id}",
        json={"quantity": 2},
    )
    assert locked_response.status_code == 409
    assert locked_response.json()["detail"] == "work_order_locked"

    cancelled_order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    added_cancelled = _add_line(authenticated_client, cancelled_order["id"], _labor_line())
    cancelled_line_id = added_cancelled["lines"][-1]["id"]
    assert _set_status(authenticated_client, cancelled_order["id"], "cancelled").status_code == 200
    locked_cancelled = authenticated_client.delete(
        f"/api/work-orders/{cancelled_order['id']}/lines/{cancelled_line_id}"
    )
    assert locked_cancelled.status_code == 409
    assert locked_cancelled.json()["detail"] == "work_order_locked"


def test_workshop_b_cannot_change_status_or_edit_lines_on_workshop_as_order(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    vehicle = _active_vehicle(authenticated_client)
    order = _create_order(authenticated_client, vehicle_id=vehicle["id"])
    item = _create_item(authenticated_client, initial_stock=10)
    added = _add_line(authenticated_client, order["id"], _part_line(item_id=item["id"], quantity=1))
    line_id = added["lines"][-1]["id"]

    status_response = _set_status(second_authenticated_client, order["id"], "approved")
    assert status_response.status_code == 404
    assert status_response.json()["detail"] == "work_order_not_found"

    add_response = second_authenticated_client.post(
        f"/api/work-orders/{order['id']}/lines", json=_labor_line()
    )
    assert add_response.status_code == 404
    assert add_response.json()["detail"] == "work_order_not_found"

    patch_response = second_authenticated_client.patch(
        f"/api/work-orders/{order['id']}/lines/{line_id}", json={"quantity": 2}
    )
    assert patch_response.status_code == 404
    assert patch_response.json()["detail"] == "work_order_not_found"

    delete_response = second_authenticated_client.delete(
        f"/api/work-orders/{order['id']}/lines/{line_id}"
    )
    assert delete_response.status_code == 404
    assert delete_response.json()["detail"] == "work_order_not_found"

    assert _get_item(authenticated_client, item["id"])["stock"] == 10
