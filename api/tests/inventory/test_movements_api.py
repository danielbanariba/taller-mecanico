"""Tests for the stock movement ledger HTTP API (/api/inventory/movements).

Defects these catch:
- a stock cache that drifts from the sum of recorded movement deltas after
  a mixed in/out/adjust sequence (the ledger's core invariant);
- replaying the exact same movement id re-applying its delta, double
  counting an offline queue's retried request;
- a movement id reused with a different payload silently overwriting the
  first movement instead of being rejected;
- an `out` larger than the current stock being rejected (blocking a
  mechanic mid-job) instead of recording negative stock flagged for
  review;
- an item's movement history coming back in the wrong order or ignoring
  the requested limit.
"""

import uuid

from fastapi.testclient import TestClient


def _create_item(client: TestClient, **overrides: object) -> dict:
    payload = {"name": "Amortiguador delantero"}
    payload.update(overrides)
    response = client.post("/api/inventory/items", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _record(client: TestClient, movement_id: str, **overrides: object) -> "object":
    payload = {"item_id": None, "kind": "in", "quantity": 1}
    payload.update(overrides)
    return client.put(f"/api/inventory/movements/{movement_id}", json=payload)


def test_stock_equals_the_sum_of_deltas_after_a_mixed_sequence(
    authenticated_client: TestClient,
) -> None:
    item = _create_item(authenticated_client)
    item_id = item["id"]

    r1 = _record(authenticated_client, str(uuid.uuid4()), item_id=item_id, kind="in", quantity=10)
    assert r1.status_code == 201
    assert r1.json()["item"]["stock"] == 10

    r2 = _record(authenticated_client, str(uuid.uuid4()), item_id=item_id, kind="out", quantity=3)
    assert r2.status_code == 201
    assert r2.json()["item"]["stock"] == 7

    r3 = _record(
        authenticated_client, str(uuid.uuid4()), item_id=item_id, kind="adjust", quantity=5
    )
    assert r3.status_code == 201
    assert r3.json()["item"]["stock"] == 5

    fetched = authenticated_client.get(f"/api/inventory/items/{item_id}")
    assert fetched.json()["stock"] == 5


def test_replaying_the_same_movement_id_is_a_no_op(authenticated_client: TestClient) -> None:
    item = _create_item(authenticated_client)
    movement_id = str(uuid.uuid4())

    first = _record(authenticated_client, movement_id, item_id=item["id"], kind="in", quantity=4)
    assert first.status_code == 201

    replay = _record(authenticated_client, movement_id, item_id=item["id"], kind="in", quantity=4)
    assert replay.status_code == 200
    assert replay.json()["item"]["stock"] == 4

    fetched = authenticated_client.get(f"/api/inventory/items/{item['id']}")
    assert fetched.json()["stock"] == 4


def test_same_movement_id_with_a_different_payload_is_rejected(
    authenticated_client: TestClient,
) -> None:
    item = _create_item(authenticated_client)
    movement_id = str(uuid.uuid4())

    first = _record(authenticated_client, movement_id, item_id=item["id"], kind="in", quantity=4)
    assert first.status_code == 201

    conflicting = _record(
        authenticated_client, movement_id, item_id=item["id"], kind="in", quantity=9
    )
    assert conflicting.status_code == 409
    assert conflicting.json()["detail"] == "movement_id_conflict"

    fetched = authenticated_client.get(f"/api/inventory/items/{item['id']}")
    assert fetched.json()["stock"] == 4


def test_an_out_larger_than_stock_allows_negative_stock_and_flags_it(
    authenticated_client: TestClient,
) -> None:
    item = _create_item(authenticated_client, initial_stock=2)

    response = _record(
        authenticated_client, str(uuid.uuid4()), item_id=item["id"], kind="out", quantity=5
    )

    assert response.status_code == 201
    body = response.json()
    assert body["item"]["stock"] == -3
    assert body["item"]["needs_review"] is True

    fetched = authenticated_client.get(f"/api/inventory/items/{item['id']}")
    assert fetched.json()["needs_review"] is True


def test_item_history_is_newest_first_and_respects_the_limit(
    authenticated_client: TestClient,
) -> None:
    item = _create_item(authenticated_client)
    for quantity in (1, 2, 3):
        response = _record(
            authenticated_client,
            str(uuid.uuid4()),
            item_id=item["id"],
            kind="in",
            quantity=quantity,
        )
        assert response.status_code == 201

    history = authenticated_client.get(
        f"/api/inventory/items/{item['id']}/movements", params={"limit": 2}
    )

    assert history.status_code == 200
    entries = history.json()
    assert len(entries) == 2
    assert [entry["quantity"] for entry in entries] == [3, 2]
