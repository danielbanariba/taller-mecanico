"""Tests for the fiscal profile and invoicing settings readiness
(`fiscal-profile` spec, AD-3).
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


def _save_profile(client: TestClient, **overrides: str) -> Response:
    payload = {**_PROFILE_PAYLOAD, **overrides}
    return client.put("/api/invoicing/profile", json=payload)


def _insert_cai_range(
    db_session: Session,
    *,
    workshop_id: str,
    created_by: str,
    issue_deadline: date,
    next_number: int = 1,
    range_end: int = 500,
) -> str:
    """Inserted directly with raw SQL: `PA.S4` is what builds range
    registration, so no repository exists yet for this test's setup.
    """
    range_id = str(uuid.uuid4())
    db_session.execute(
        text(
            "INSERT INTO cai_ranges ("
            "    id, workshop_id, document_type, cai, establishment_code, emission_point_code,"
            "    range_start, range_end, next_number, issue_deadline, created_by,"
            "    created_at, updated_at"
            ") VALUES ("
            "    :id, :workshop_id, '01', 'AAAA0101010101010101', '001', '001',"
            "    1, :range_end, :next_number, :issue_deadline, :created_by, now(), now()"
            ")"
        ),
        {
            "id": range_id,
            "workshop_id": workshop_id,
            "range_end": range_end,
            "next_number": next_number,
            "issue_deadline": issue_deadline,
            "created_by": created_by,
        },
    )
    db_session.commit()
    return range_id


def test_saving_a_complete_profile_for_the_first_time_stores_it(authenticated_client: TestClient):
    """Defect it catches: an incomplete profile is accepted as ready,
    or the stored RTN keeps its separators instead of 14 bare digits.
    """
    response = _save_profile(authenticated_client)
    assert response.status_code == 201
    body = response.json()
    assert body["rtn"] == "08011990123456"
    assert body["establishment_code"] == "001"


def test_an_rtn_that_is_not_14_digits_after_stripping_separators_is_rejected(
    authenticated_client: TestClient,
):
    response = _save_profile(authenticated_client, rtn="0801-1990-12345")
    assert response.status_code == 422
    assert response.json()["detail"] == "invalid_rtn"
    assert authenticated_client.get("/api/invoicing/settings").json()["profile"] is None


def test_a_workshop_that_never_saves_a_profile_has_no_row(authenticated_client: TestClient):
    """Defect it catches: a stub profile is created on first read
    instead of reporting "no profile" (`fiscal-profile` spec).
    """
    response = authenticated_client.get("/api/invoicing/settings")
    assert response.status_code == 200
    assert response.json()["profile"] is None


def test_repeating_an_identical_save_changes_nothing(authenticated_client: TestClient):
    """Defect it catches: an upsert duplicates the row, or a replay
    corrupts a field it was never meant to touch.
    """
    first = _save_profile(authenticated_client).json()
    second = _save_profile(authenticated_client)
    assert second.status_code == 200
    body = second.json()
    assert body["rtn"] == first["rtn"]
    assert body["legal_name"] == first["legal_name"]
    assert body["phone"] == first["phone"]


def test_a_later_save_updates_only_the_fields_that_changed(authenticated_client: TestClient):
    """Defect it catches: an upsert overwrites an untouched field with
    a blank or a stale value instead of what the request actually sent.
    """
    _save_profile(authenticated_client)
    updated = _save_profile(authenticated_client, phone="2200-9900")
    assert updated.status_code == 200
    body = updated.json()
    assert body["phone"] == "22009900"
    assert body["legal_name"] == _PROFILE_PAYLOAD["legal_name"]


def test_editing_the_codes_before_any_range_exists_succeeds(authenticated_client: TestClient):
    _save_profile(authenticated_client)
    response = _save_profile(authenticated_client, emission_point_code="002")
    assert response.status_code == 200
    assert response.json()["emission_point_code"] == "002"


def test_editing_the_codes_while_an_active_range_exists_is_rejected(
    authenticated_client: TestClient, db_session: Session
):
    """Defect it catches: a CAI prints under codes SAR never granted it,
    because the profile silently let its codes change mid-range.
    """
    _save_profile(authenticated_client)
    me = authenticated_client.get("/api/auth/me").json()
    _insert_cai_range(
        db_session,
        workshop_id=me["workshop"]["id"],
        created_by=me["user"]["id"],
        issue_deadline=date.today() + timedelta(days=300),
    )

    response = _save_profile(authenticated_client, emission_point_code="002")
    assert response.status_code == 409
    assert response.json()["detail"] == "fiscal_profile_codes_locked"


def test_editing_the_codes_once_every_range_is_exhausted_or_expired_is_allowed(
    authenticated_client: TestClient, db_session: Session
):
    """Defect it catches: the codes stay permanently locked after
    every range finishes, blocking a legitimate later correction.
    """
    _save_profile(authenticated_client)
    me = authenticated_client.get("/api/auth/me").json()
    _insert_cai_range(
        db_session,
        workshop_id=me["workshop"]["id"],
        created_by=me["user"]["id"],
        issue_deadline=date.today() + timedelta(days=300),
        next_number=501,
        range_end=500,
    )

    response = _save_profile(authenticated_client, emission_point_code="002")
    assert response.status_code == 200
    assert response.json()["emission_point_code"] == "002"


def test_another_workshops_profile_is_invisible(authenticated_client: TestClient):
    """Defect it catches: a missing `workshop_id` filter leaks fiscal
    data to a different tenant.
    """
    _save_profile(authenticated_client)

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

    settings = authenticated_client.get("/api/invoicing/settings")
    assert settings.json()["profile"] is None


def test_settings_with_no_profile_reports_fiscal_profile_missing(authenticated_client: TestClient):
    """Defect it catches: the settings endpoint and issuance
    eligibility can disagree because they are not backed by one
    shared readiness function.
    """
    response = authenticated_client.get("/api/invoicing/settings")
    documents = response.json()["documents"]
    assert documents[0]["document_type"] == "01"
    assert documents[0]["ready"] is False
    assert documents[0]["blocked_reason"] == "fiscal_profile_missing"


def test_settings_with_a_complete_profile_and_no_range_reports_cai_range_missing(
    authenticated_client: TestClient,
):
    _save_profile(authenticated_client)
    response = authenticated_client.get("/api/invoicing/settings")
    documents = response.json()["documents"]
    assert documents[0]["ready"] is False
    assert documents[0]["blocked_reason"] == "cai_range_missing"


def test_settings_with_a_complete_profile_and_an_active_range_is_ready(
    authenticated_client: TestClient, db_session: Session
):
    """Defect it catches: readiness never flips to true even once both
    conditions are met, blocking issuance forever.
    """
    _save_profile(authenticated_client)
    me = authenticated_client.get("/api/auth/me").json()
    _insert_cai_range(
        db_session,
        workshop_id=me["workshop"]["id"],
        created_by=me["user"]["id"],
        issue_deadline=date.today() + timedelta(days=300),
    )

    response = authenticated_client.get("/api/invoicing/settings")
    documents = response.json()["documents"]
    assert documents[0]["ready"] is True
    assert documents[0]["blocked_reason"] is None
    assert documents[0]["next_number"] == "001-001-01-00000001"
