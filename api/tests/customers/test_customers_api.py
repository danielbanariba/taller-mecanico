"""Tests for the customers HTTP API (/api/customers).

Defects these catch:
- the customer path skips `PhoneNumber` normalization, or invalid phones
  (too short, or starting with a digit `PhoneNumber` never accepts) are
  persisted instead of rejected with `invalid_phone`;
- an empty phone is rejected or crashes normalization, instead of saving
  a customer with no phone at all;
- a retry of `POST /customers` with the same id and payload duplicates the
  customer (not idempotent), or a conflicting replay silently overwrites
  the original data instead of returning a 409;
- a partial `PATCH` clobbers fields the caller omitted, or tenancy is
  unchecked on edit so a foreign/nonexistent id does not 404;
- an archive hard-deletes the customer (losing its history) instead of
  soft-archiving it, still shows up in the default listing, or a repeated
  archive re-stamps `archived_at`;
- search is accent- or case-sensitive, the phone fragment is not matched,
  or a search term with `%`/`_` is used as a raw `LIKE` wildcard instead
  of matching those characters literally;
- a missing `workshop_id` filter leaks or mutates another workshop's
  customer.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from taller.main import app


@pytest.fixture
def second_authenticated_client(client: TestClient) -> Generator[TestClient]:
    """A second TestClient, authenticated as an independent second workshop.

    Mirrors `test_tenant_isolation.second_authenticated_client`.
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


def test_a_landline_phone_is_normalized_and_classified(authenticated_client: TestClient) -> None:
    body = _create_customer(authenticated_client, phone="+504 2234-5678")

    assert body["phone"] == "22345678"
    assert body["phone_is_mobile"] is False


def test_a_7_digit_or_1_prefixed_phone_is_rejected(authenticated_client: TestClient) -> None:
    short_response = authenticated_client.post(
        "/api/customers", json={"full_name": "Jose Nunez", "phone": "1234567"}
    )
    assert short_response.status_code == 422
    assert short_response.json()["detail"] == "invalid_phone"

    one_prefixed_response = authenticated_client.post(
        "/api/customers", json={"full_name": "Jose Nunez", "phone": "12345678"}
    )
    assert one_prefixed_response.status_code == 422
    assert one_prefixed_response.json()["detail"] == "invalid_phone"

    listing = authenticated_client.get("/api/customers")
    assert listing.json() == []


def test_an_empty_phone_is_accepted_with_no_mobile_classification(
    authenticated_client: TestClient,
) -> None:
    body = _create_customer(authenticated_client, full_name="Carlos Mejia", phone=None)

    assert body["phone"] is None
    assert body["phone_is_mobile"] is None


def test_replaying_an_identical_create_is_a_no_op(authenticated_client: TestClient) -> None:
    client_id = "11111111-1111-1111-1111-111111111111"
    first = authenticated_client.post(
        "/api/customers", json={"id": client_id, "full_name": "Ana Castillo", "phone": "98765432"}
    )
    assert first.status_code == 201

    replay = authenticated_client.post(
        "/api/customers", json={"id": client_id, "full_name": "Ana Castillo", "phone": "98765432"}
    )
    assert replay.status_code == 200
    assert replay.json() == first.json()

    listing = authenticated_client.get("/api/customers")
    assert len(listing.json()) == 1


def test_replaying_an_id_with_a_different_payload_is_a_conflict(
    authenticated_client: TestClient,
) -> None:
    client_id = "22222222-2222-2222-2222-222222222222"
    original = authenticated_client.post(
        "/api/customers", json={"id": client_id, "full_name": "Luis Zelaya"}
    )
    assert original.status_code == 201

    conflicting = authenticated_client.post(
        "/api/customers", json={"id": client_id, "full_name": "Another Name"}
    )
    assert conflicting.status_code == 409
    assert conflicting.json()["detail"] == "customer_id_conflict"

    fetched = authenticated_client.get(f"/api/customers/{client_id}")
    assert fetched.json()["full_name"] == "Luis Zelaya"


def test_editing_only_the_name_leaves_phone_unchanged(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client, full_name="Maria Hernandez", phone="98765432")

    response = authenticated_client.patch(
        f"/api/customers/{customer['id']}", json={"full_name": "Maria H. Hernandez"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Maria H. Hernandez"
    assert body["phone"] == "98765432"
    assert body["phone_is_mobile"] is True


def test_editing_a_nonexistent_customer_is_not_found(authenticated_client: TestClient) -> None:
    missing_id = "33333333-3333-3333-3333-333333333333"

    response = authenticated_client.patch(f"/api/customers/{missing_id}", json={"full_name": "X"})

    assert response.status_code == 404
    assert response.json()["detail"] == "customer_not_found"


def test_patching_full_name_to_an_explicit_null_is_a_clean_validation_error(
    authenticated_client: TestClient,
) -> None:
    """Defect this catches: `full_name` is typed `str | None` only so the

    field can be omitted; without a guard rejecting an explicit `null`,
    `update_customer` calls `.strip()` on `None` and crashes with an
    unhandled 500 instead of a 422, and the customer's name is left
    unaffected either way.
    """
    customer = _create_customer(authenticated_client, full_name="Maria Hernandez")

    response = authenticated_client.patch(
        f"/api/customers/{customer['id']}", json={"full_name": None}
    )

    assert response.status_code == 422
    unaffected = authenticated_client.get(f"/api/customers/{customer['id']}")
    assert unaffected.json()["full_name"] == "Maria Hernandez"


def test_archiving_an_active_customer_hides_it_from_the_default_listing(
    authenticated_client: TestClient,
) -> None:
    customer = _create_customer(authenticated_client)

    archive_response = authenticated_client.post(f"/api/customers/{customer['id']}/archive")
    assert archive_response.status_code == 204

    fetched = authenticated_client.get(f"/api/customers/{customer['id']}")
    assert fetched.json()["archived_at"] is not None

    listing = authenticated_client.get("/api/customers")
    assert customer["id"] not in [row["id"] for row in listing.json()]


def test_archiving_twice_keeps_the_first_archived_at(authenticated_client: TestClient) -> None:
    customer = _create_customer(authenticated_client)

    first_archive = authenticated_client.post(f"/api/customers/{customer['id']}/archive")
    assert first_archive.status_code == 204
    first_archived_at = authenticated_client.get(f"/api/customers/{customer['id']}").json()[
        "archived_at"
    ]

    second_archive = authenticated_client.post(f"/api/customers/{customer['id']}/archive")
    assert second_archive.status_code == 204
    second_archived_at = authenticated_client.get(f"/api/customers/{customer['id']}").json()[
        "archived_at"
    ]

    assert second_archived_at == first_archived_at


def test_search_is_accent_insensitive(authenticated_client: TestClient) -> None:
    _create_customer(authenticated_client, full_name="María Hernández")
    _create_customer(authenticated_client, full_name="Carlos Mejía")

    response = authenticated_client.get("/api/customers", params={"q": "maria"})

    assert response.status_code == 200
    names = [row["full_name"] for row in response.json()]
    assert names == ["María Hernández"]


def test_search_matches_a_phone_fragment(authenticated_client: TestClient) -> None:
    _create_customer(authenticated_client, full_name="Ana Castillo", phone="98765432")
    _create_customer(authenticated_client, full_name="Luis Zelaya", phone="22001100")

    response = authenticated_client.get("/api/customers", params={"q": "9876"})

    names = [row["full_name"] for row in response.json()]
    assert names == ["Ana Castillo"]


def test_search_underscore_and_percent_match_only_literally(
    authenticated_client: TestClient,
) -> None:
    literal_match = _create_customer(authenticated_client, full_name="Descuento 50%")
    _create_customer(authenticated_client, full_name="Descuento especial")

    response = authenticated_client.get("/api/customers", params={"q": "50%"})

    assert [row["id"] for row in response.json()] == [literal_match["id"]]


def test_another_workshops_customer_is_invisible(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    customer = _create_customer(authenticated_client)

    get_response = second_authenticated_client.get(f"/api/customers/{customer['id']}")
    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "customer_not_found"

    list_response = second_authenticated_client.get("/api/customers")
    assert customer["id"] not in [row["id"] for row in list_response.json()]


def test_another_workshops_customer_cannot_be_mutated(
    authenticated_client: TestClient, second_authenticated_client: TestClient
) -> None:
    customer = _create_customer(authenticated_client)

    patch_response = second_authenticated_client.patch(
        f"/api/customers/{customer['id']}", json={"full_name": "Hijacked"}
    )
    archive_response = second_authenticated_client.post(f"/api/customers/{customer['id']}/archive")

    assert patch_response.status_code == 404
    assert patch_response.json()["detail"] == "customer_not_found"
    assert archive_response.status_code == 404
    assert archive_response.json()["detail"] == "customer_not_found"

    unaffected = authenticated_client.get(f"/api/customers/{customer['id']}")
    assert unaffected.json()["full_name"] == "Maria Hernandez"
    assert unaffected.json()["archived_at"] is None
