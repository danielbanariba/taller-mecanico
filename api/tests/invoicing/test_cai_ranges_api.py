"""Tests for CAI range registration and correction (`cai-ranges` spec, AD-4).

Identical bounds on a different document type being allowed is covered
at the domain level by `test_range_selection.py`'s `overlaps()` tests.
"""

import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

_PROFILE_PAYLOAD = {
    "rtn": "0801-1990-123456",
    "legal_name": "Taller Don Chepe S. de R.L.",
    "trade_name": "Taller Don Chepe",
    "address": "Barrio El Centro, Tegucigalpa",
    "phone": "2200-1100",
    "email": "contacto@tallerdonchepe.example",
    "establishment_code": "001",
    "emission_point_code": "001",
}


def _save_profile(client: TestClient) -> None:
    response = client.put("/api/invoicing/profile", json=_PROFILE_PAYLOAD)
    assert response.status_code == 201, response.text


def _range_payload(**overrides: object) -> dict:
    payload = {
        "id": str(uuid.uuid4()),
        "document_type": "01",
        "cai": "A1B2C3D4E5",
        "range_start": 1,
        "range_end": 100,
        "issue_deadline": (date.today() + timedelta(days=300)).isoformat(),
    }
    payload.update(overrides)
    return payload


def _create_range(client: TestClient, **overrides: object) -> Response:
    return client.post("/api/invoicing/cai-ranges", json=_range_payload(**overrides))


def test_registering_a_factura_range_starts_next_correlative_at_range_start(
    authenticated_client: TestClient,
):
    """Defect it catches: `next_correlative` starts anywhere other than
    `range_start`.
    """
    _save_profile(authenticated_client)
    response = _create_range(authenticated_client)
    assert response.status_code == 201
    body = response.json()
    assert body["next_number"] == 1
    assert body["document_type"] == "01"
    assert body["first_number"] == "001-001-01-00000001"
    assert body["last_number"] == "001-001-01-00000100"


def test_registering_a_range_with_no_profile_is_rejected(authenticated_client: TestClient):
    """Defect it catches: a range is created with empty or missing
    establecimiento/punto de emisión codes because no profile was ever
    locked to copy them from.
    """
    response = _create_range(authenticated_client)
    assert response.status_code == 409
    assert response.json()["detail"] == "fiscal_profile_missing"


def test_a_credit_note_range_is_accepted_in_phase_b(authenticated_client: TestClient):
    """Defect it catches: `create_range` still carries phase A's
    `unsupported_document_type` gate, blocking the `06` ranges phase B's
    credit notes need.
    """
    _save_profile(authenticated_client)
    response = _create_range(authenticated_client, document_type="06")
    assert response.status_code == 201
    body = response.json()
    assert body["document_type"] == "06"


def test_replaying_an_identical_registration_is_a_noop(authenticated_client: TestClient):
    """Defect it catches: a retried registration duplicates the range row."""
    _save_profile(authenticated_client)
    payload = _range_payload()
    first = authenticated_client.post("/api/invoicing/cai-ranges", json=payload)
    assert first.status_code == 201

    second = authenticated_client.post("/api/invoicing/cai-ranges", json=payload)
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]


def test_reusing_a_range_id_with_a_different_payload_is_a_conflict(
    authenticated_client: TestClient,
):
    """Defect it catches: a retry with a changed payload silently
    overwrites a CAI authorization instead of being rejected.
    """
    _save_profile(authenticated_client)
    range_id = str(uuid.uuid4())
    first = _create_range(authenticated_client, id=range_id)
    assert first.status_code == 201

    conflict = _create_range(authenticated_client, id=range_id, cai="Z9Z9Z9Z9Z9")
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == "cai_range_id_conflict"


def test_an_overlapping_range_of_the_same_type_is_rejected(authenticated_client: TestClient):
    """Defect it catches: two overlapping ranges would later allocate
    the same correlative under two different CAIs.
    """
    _save_profile(authenticated_client)
    first = _create_range(authenticated_client, range_start=1, range_end=100)
    assert first.status_code == 201

    response = _create_range(authenticated_client, range_start=50, range_end=150)
    assert response.status_code == 409
    assert response.json()["detail"] == "cai_range_overlap"


def test_adjacent_ranges_of_the_same_type_do_not_overlap(authenticated_client: TestClient):
    """Defect it catches: a valid, non-overlapping consecutive range is
    rejected by an off-by-one in the overlap check.
    """
    _save_profile(authenticated_client)
    first = _create_range(authenticated_client, range_start=1, range_end=500)
    assert first.status_code == 201

    response = _create_range(authenticated_client, range_start=501, range_end=1000)
    assert response.status_code == 201


def test_editing_an_untouched_range_succeeds(authenticated_client: TestClient):
    _save_profile(authenticated_client)
    created = _create_range(authenticated_client).json()

    new_deadline = (date.today() + timedelta(days=200)).isoformat()
    response = authenticated_client.patch(
        f"/api/invoicing/cai-ranges/{created['id']}", json={"issue_deadline": new_deadline}
    )
    assert response.status_code == 200
    assert response.json()["issue_deadline"] == new_deadline


def test_editing_an_untouched_credit_note_range_succeeds(authenticated_client: TestClient):
    """Defect it catches: `update_range` still carries phase A's
    `unsupported_document_type` gate (`fields.get("document_type",
    cai_range.document_type)` falls back to the stored `06` and the
    unconditional check fires anyway), so a PATCH that never even
    touches `document_type` is rejected for every `06` range -- the
    only correction path there is for one, since there is no DELETE.
    """
    _save_profile(authenticated_client)
    created = _create_range(authenticated_client, document_type="06").json()

    new_deadline = (date.today() + timedelta(days=200)).isoformat()
    response = authenticated_client.patch(
        f"/api/invoicing/cai-ranges/{created['id']}", json={"issue_deadline": new_deadline}
    )
    assert response.status_code == 200
    assert response.json()["issue_deadline"] == new_deadline
    assert response.json()["document_type"] == "06"


def test_editing_a_range_that_has_issued_a_document_is_rejected(
    authenticated_client: TestClient, db_session: Session
):
    """Defect it catches: a used CAI is silently rewritten after at
    least one number has already been allocated from it.
    """
    _save_profile(authenticated_client)
    created = _create_range(authenticated_client).json()
    db_session.execute(
        text("UPDATE cai_ranges SET next_number = next_number + 1 WHERE id = :id"),
        {"id": created["id"]},
    )
    db_session.commit()

    response = authenticated_client.patch(
        f"/api/invoicing/cai-ranges/{created['id']}", json={"cai": "Z9Z9Z9Z9Z9"}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "cai_range_immutable"


def test_range_start_greater_than_range_end_is_rejected(authenticated_client: TestClient):
    _save_profile(authenticated_client)
    response = _create_range(authenticated_client, range_start=100, range_end=1)
    assert response.status_code == 422
    assert response.json()["detail"] == "invalid_cai_range"


def test_range_end_above_the_maximum_is_rejected(authenticated_client: TestClient):
    _save_profile(authenticated_client)
    response = _create_range(authenticated_client, range_start=1, range_end=100_000_000)
    assert response.status_code == 422
    assert response.json()["detail"] == "invalid_cai_range"


def test_a_past_issue_deadline_is_rejected(authenticated_client: TestClient):
    """Defect it catches: a typo deadline in the past (the wrong year)
    is accepted and later printed on a document.
    """
    _save_profile(authenticated_client)
    response = _create_range(
        authenticated_client, issue_deadline=(date.today() - timedelta(days=1)).isoformat()
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "cai_deadline_passed"


def test_an_issue_deadline_more_than_a_year_out_is_rejected(authenticated_client: TestClient):
    """Defect it catches: a typo deadline in the future (the wrong
    year) is accepted even though a CAI is valid for at most one year.
    """
    _save_profile(authenticated_client)
    response = _create_range(
        authenticated_client, issue_deadline=(date.today() + timedelta(days=367)).isoformat()
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "cai_deadline_too_far"


def test_another_workshops_range_is_invisible(authenticated_client: TestClient):
    """Defect it catches: a missing `workshop_id` filter leaks or
    mutates another tenant's CAI.
    """
    _save_profile(authenticated_client)
    created = _create_range(authenticated_client).json()

    registered_as_b = authenticated_client.post(
        "/api/auth/register",
        json={
            "workshop_name": "Taller Vecino",
            "owner_name": "Otro Propietario",
            "phone": "9911-2233",
            "password": "another-strong-password",
        },
    )
    assert registered_as_b.status_code == 201

    response = authenticated_client.patch(
        f"/api/invoicing/cai-ranges/{created['id']}", json={"cai": "Z9Z9Z9Z9Z9"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "cai_range_not_found"


def test_a_registered_range_appears_in_settings_with_its_state(authenticated_client: TestClient):
    """Defect it catches: the settings endpoint and range registration
    disagree because `GET /invoicing/settings` never surfaces a
    registered range at all.
    """
    _save_profile(authenticated_client)
    created = _create_range(authenticated_client).json()

    response = authenticated_client.get("/api/invoicing/settings")
    ranges = response.json()["ranges"]
    assert len(ranges) == 1
    assert ranges[0]["id"] == created["id"]
    assert ranges[0]["state"] == "active"


def test_a_factura_range_and_a_credit_note_range_are_both_active_in_settings(
    authenticated_client: TestClient,
):
    """Defect it catches: settings deriving range states across every
    document type at once, so a usable `01` range and a usable `06`
    range compete for one `active` slot and one of them is reported as
    standby, disagreeing with the range's own registration response.
    """
    _save_profile(authenticated_client)
    invoice_range = _create_range(authenticated_client).json()
    credit_note_range = _create_range(
        authenticated_client,
        document_type="06",
        issue_deadline=(date.today() + timedelta(days=200)).isoformat(),
    ).json()

    response = authenticated_client.get("/api/invoicing/settings")
    states = {r["id"]: r["state"] for r in response.json()["ranges"]}
    assert states == {invoice_range["id"]: "active", credit_note_range["id"]: "active"}
