"""Tests for the `fiscal_invoices` immutability trigger
(`taller_fiscal_invoice_guard`, design.md's AD-10).

No application code issues a Factura yet (that lands in `PA.S5`), so
these rows are inserted directly with raw SQL -- the same pattern
`test_login_throttle_repository.py` uses for a table with no repository
of its own yet.

Defect this catches: an application bug or an ad-hoc script rewrites or
deletes a legal document instead of being blocked at the database level
(Art. 5, 41, 43) -- the kind of mistake no amount of application-layer
discipline alone can rule out.
"""

import uuid
from collections.abc import Generator
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

#: A clean L 1,000.00 total (AD-8's worked table): gravado L 869.57 / ISV
#: L 130.43, summing exactly to the total in integer cents.
_TOTAL_CENTS = 100000
_TAXABLE_15_CENTS = 86957
_ISV_15_CENTS = 13043


def _order_context(client: TestClient) -> dict[str, object]:
    me = client.get("/api/auth/me").json()
    customer = client.post("/api/customers", json={"full_name": "Maria Hernandez"}).json()
    vehicle = client.post(
        "/api/vehicles",
        json={"customer_id": customer["id"], "vehicle_type": "car", "make": "Toyota"},
    ).json()
    order = client.post(
        "/api/work-orders", json={"id": str(uuid.uuid4()), "vehicle_id": vehicle["id"]}
    ).json()
    return {
        "workshop_id": me["workshop"]["id"],
        "user_id": me["user"]["id"],
        "order_id": order["id"],
        "order_number": order["number"],
    }


def _insert_cai_range(db_session: Session, *, workshop_id: str, created_by: str) -> str:
    range_id = str(uuid.uuid4())
    db_session.execute(
        text(
            "INSERT INTO cai_ranges ("
            "    id, workshop_id, document_type, cai, establishment_code, emission_point_code,"
            "    range_start, range_end, next_number, issue_deadline, created_by,"
            "    created_at, updated_at"
            ") VALUES ("
            "    :id, :workshop_id, '01', 'AAAA0101010101010101', '001', '001',"
            "    1, 500, 2, :issue_deadline, :created_by, now(), now()"
            ")"
        ),
        {
            "id": range_id,
            "workshop_id": workshop_id,
            "issue_deadline": date.today() + timedelta(days=300),
            "created_by": created_by,
        },
    )
    db_session.commit()
    return range_id


def _insert_fiscal_invoice(
    db_session: Session,
    *,
    workshop_id: str,
    order_id: str,
    order_number: int,
    cai_range_id: str,
    created_by: str,
) -> str:
    invoice_id = str(uuid.uuid4())
    db_session.execute(
        text(
            "INSERT INTO fiscal_invoices ("
            "    id, workshop_id, order_id, order_number, cai_range_id, correlative, number,"
            "    issued_at, issue_date, issuer_rtn, issuer_legal_name, issuer_trade_name,"
            "    issuer_address, issuer_phone, issuer_email, cai, range_first_number,"
            "    range_last_number, issue_deadline, buyer_name, buyer_rtn, exempt_cents,"
            "    exonerated_cents, discount_cents, taxable_15_cents, isv_15_cents, total_cents,"
            "    total_in_words, credited_at, created_by, created_at"
            ") VALUES ("
            "    :id, :workshop_id, :order_id, :order_number, :cai_range_id, 1,"
            "    '001-001-01-00000001', now(), CURRENT_DATE, '08011990123456',"
            "    'Taller Don Chepe S. de R.L.', 'Taller Don Chepe', 'Barrio El Centro',"
            "    '22001100', 'taller@example.com', 'AAAA0101010101010101',"
            "    '001-001-01-00000001', '001-001-01-00000500', :issue_deadline, NULL, NULL,"
            "    0, 0, 0, :taxable_15_cents, :isv_15_cents, :total_cents,"
            "    'UN MIL LEMPIRAS CON 00/100', NULL, :created_by, now()"
            ")"
        ),
        {
            "id": invoice_id,
            "workshop_id": workshop_id,
            "order_id": order_id,
            "order_number": order_number,
            "cai_range_id": cai_range_id,
            "issue_deadline": date.today() + timedelta(days=300),
            "taxable_15_cents": _TAXABLE_15_CENTS,
            "isv_15_cents": _ISV_15_CENTS,
            "total_cents": _TOTAL_CENTS,
            "created_by": created_by,
        },
    )
    db_session.commit()
    return invoice_id


@pytest.fixture
def issued_invoice(authenticated_client: TestClient, db_session: Session) -> Generator[str]:
    context = _order_context(authenticated_client)
    range_id = _insert_cai_range(
        db_session, workshop_id=context["workshop_id"], created_by=context["user_id"]
    )
    invoice_id = _insert_fiscal_invoice(
        db_session,
        workshop_id=context["workshop_id"],
        order_id=context["order_id"],
        order_number=context["order_number"],
        cai_range_id=range_id,
        created_by=context["user_id"],
    )
    yield invoice_id


def test_updating_any_field_other_than_crediting_is_rejected(
    issued_invoice: str, db_session: Session
) -> None:
    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE fiscal_invoices SET total_cents = 1 WHERE id = :id"),
            {"id": issued_invoice},
        )
    db_session.rollback()

    unchanged = db_session.execute(
        text("SELECT total_cents FROM fiscal_invoices WHERE id = :id"), {"id": issued_invoice}
    ).scalar_one()
    assert unchanged == _TOTAL_CENTS


def test_deleting_an_issued_invoice_is_rejected(issued_invoice: str, db_session: Session) -> None:
    with pytest.raises(DBAPIError):
        db_session.execute(
            text("DELETE FROM fiscal_invoices WHERE id = :id"), {"id": issued_invoice}
        )
    db_session.rollback()

    still_there = db_session.execute(
        text("SELECT 1 FROM fiscal_invoices WHERE id = :id"), {"id": issued_invoice}
    ).scalar_one_or_none()
    assert still_there == 1


def test_crediting_once_succeeds_and_a_second_time_is_rejected(
    issued_invoice: str, db_session: Session
) -> None:
    # Bound, distinct Python timestamps rather than SQL `now()`: `now()` is
    # frozen to the start of the enclosing Postgres transaction, and this
    # whole test runs in one (the outer SAVEPOINT-joined transaction), so
    # two `now()` calls would read back equal and the second UPDATE would
    # be a harmless no-op instead of the disallowed second credit.
    first_credit = datetime.now(UTC)
    second_credit = first_credit + timedelta(seconds=1)

    db_session.execute(
        text("UPDATE fiscal_invoices SET credited_at = :credited_at WHERE id = :id"),
        {"id": issued_invoice, "credited_at": first_credit},
    )
    db_session.commit()

    with pytest.raises(DBAPIError):
        db_session.execute(
            text("UPDATE fiscal_invoices SET credited_at = :credited_at WHERE id = :id"),
            {"id": issued_invoice, "credited_at": second_credit},
        )
    db_session.rollback()

    credited_at = db_session.execute(
        text("SELECT credited_at FROM fiscal_invoices WHERE id = :id"), {"id": issued_invoice}
    ).scalar_one()
    assert credited_at is not None
