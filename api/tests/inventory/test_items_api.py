"""Tests for the inventory items HTTP API (/api/inventory/items).

Defects these catch:
- a create endpoint that doesn't actually persist every field it accepts,
  so the response looks right but a later GET returns stale defaults;
- a duplicate-name guard that only checks exact byte-for-byte equality,
  letting "Bateria" and "BATERÍA" coexist as two "different" items;
- a search implementation that is case- or accent-sensitive, so a mechanic
  typing without accents on a phone keyboard finds nothing;
- a low-stock filter that includes items with no minimum configured, or
  excludes an item that is exactly at its minimum;
- an archive that deletes the item (losing its history) instead of hiding
  it, or that still shows up in the default list;
- a PATCH that silently lets the client overwrite `stock` directly,
  bypassing the movement ledger that is supposed to be the only source of
  truth for it;
- an endpoint reachable without a valid session, leaking another
  workshop's inventory existence/shape to an anonymous caller.
"""

from fastapi.testclient import TestClient


def _create_item(client: TestClient, **overrides: object) -> dict:
    payload = {"name": "Filtro de aceite", "category": "Filtros", "unit": "unidad"}
    payload.update(overrides)
    response = client.post("/api/inventory/items", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_item_persists_every_submitted_field(authenticated_client: TestClient) -> None:
    body = _create_item(
        authenticated_client,
        name="Aceite 20W-50",
        category="Lubricantes",
        unit="galon",
        min_stock=3,
        sale_price_cents=25000,
        notes="Marca Mobil",
    )

    assert body["name"] == "Aceite 20W-50"
    assert body["category"] == "Lubricantes"
    assert body["unit"] == "galon"
    assert body["min_stock"] == 3
    assert body["sale_price_cents"] == 25000
    assert body["notes"] == "Marca Mobil"
    assert body["stock"] == 0
    assert body["needs_review"] is False
    assert body["archived_at"] is None

    fetched = authenticated_client.get(f"/api/inventory/items/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_initial_stock_records_an_adjustment_as_the_first_history_entry(
    authenticated_client: TestClient,
) -> None:
    item = _create_item(authenticated_client, name="Bujia NGK", initial_stock=5)
    assert item["stock"] == 5

    history = authenticated_client.get(f"/api/inventory/items/{item['id']}/movements")
    assert history.status_code == 200
    entries = history.json()
    assert len(entries) == 1
    assert entries[0]["kind"] == "adjust"
    assert entries[0]["quantity"] == 5
    assert entries[0]["delta"] == 5
    assert entries[0]["note"] == "Inventario inicial"


def test_duplicate_active_name_is_rejected_case_and_accent_insensitive(
    authenticated_client: TestClient,
) -> None:
    _create_item(authenticated_client, name="Bateria 12V")

    response = authenticated_client.post("/api/inventory/items", json={"name": "BATERÍA 12v"})

    assert response.status_code == 409
    assert response.json()["detail"] == "item_name_taken"


def test_search_is_case_and_accent_insensitive(authenticated_client: TestClient) -> None:
    item = _create_item(authenticated_client, name="Bateria de moto")
    _create_item(authenticated_client, name="Casco integral")

    response = authenticated_client.get("/api/inventory/items", params={"q": "batería"})

    assert response.status_code == 200
    names = [row["name"] for row in response.json()]
    assert names == [item["name"]]


def test_low_stock_filter_returns_only_items_at_or_below_their_minimum(
    authenticated_client: TestClient,
) -> None:
    low = _create_item(
        authenticated_client, name="Pastillas de freno", min_stock=4, initial_stock=4
    )
    _create_item(authenticated_client, name="Llanta 175/65", min_stock=2, initial_stock=10)
    _create_item(authenticated_client, name="Aceite de caja")  # no minimum configured

    response = authenticated_client.get("/api/inventory/items", params={"low_stock": "true"})

    assert response.status_code == 200
    ids = [row["id"] for row in response.json()]
    assert ids == [low["id"]]


def test_archived_items_are_hidden_by_default_and_visible_with_include_archived(
    authenticated_client: TestClient,
) -> None:
    item = _create_item(authenticated_client, name="Filtro de aire viejo")

    archive_response = authenticated_client.post(f"/api/inventory/items/{item['id']}/archive")
    assert archive_response.status_code == 204

    default_list = authenticated_client.get("/api/inventory/items")
    assert item["id"] not in [row["id"] for row in default_list.json()]

    full_list = authenticated_client.get(
        "/api/inventory/items", params={"include_archived": "true"}
    )
    archived_row = next(row for row in full_list.json() if row["id"] == item["id"])
    assert archived_row["archived_at"] is not None


def test_patch_updates_fields_but_never_stock(authenticated_client: TestClient) -> None:
    item = _create_item(authenticated_client, name="Llave de cruz", initial_stock=2)

    response = authenticated_client.patch(
        f"/api/inventory/items/{item['id']}",
        json={"name": "Llave de cruz 4 puntas", "min_stock": 1, "stock": 999},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Llave de cruz 4 puntas"
    assert body["min_stock"] == 1
    assert body["stock"] == 2


def test_get_unknown_item_returns_404(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/api/inventory/items/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "item_not_found"


def test_items_endpoints_require_authentication(client: TestClient) -> None:
    list_response = client.get("/api/inventory/items")
    create_response = client.post("/api/inventory/items", json={"name": "Anything"})

    assert list_response.status_code == 401
    assert create_response.status_code == 401
