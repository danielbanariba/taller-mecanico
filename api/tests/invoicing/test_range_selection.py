"""Tests for CAI range selection and overlap (AD-4)."""

import uuid
from datetime import date, datetime, timedelta

import pytest

from taller.invoicing.domain.document_number import DocumentType
from taller.invoicing.domain.errors import CaiRangeExhausted, CaiRangeExpired, CaiRangeMissing
from taller.invoicing.domain.ranges import CaiRange, overlaps, select_range

_TODAY = date(2026, 10, 8)
_CREATED_AT = datetime(2026, 1, 1)


def _range(**overrides: object) -> CaiRange:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "workshop_id": uuid.uuid4(),
        "document_type": DocumentType.invoice,
        "cai": "CAI00000000000000000000000000000000-00",
        "establishment_code": "001",
        "emission_point_code": "001",
        "range_start": 1,
        "range_end": 100,
        "next_number": 1,
        "issue_deadline": date(2026, 12, 31),
        "created_by": uuid.uuid4(),
        "created_at": _CREATED_AT,
        "updated_at": _CREATED_AT,
    }
    defaults.update(overrides)
    return CaiRange(**defaults)


def test_an_earlier_deadline_wins_over_a_lower_range_start():
    """Defect it catches: selecting the lowest range_start instead of
    the earliest fecha límite would waste a soon-to-expire range's
    numbers (AD-4).
    """
    expires_soon = _range(range_start=501, range_end=600, issue_deadline=date(2026, 10, 10))
    expires_later = _range(range_start=1, range_end=100, issue_deadline=date(2027, 10, 10))
    chosen = select_range([expires_later, expires_soon], _TODAY)
    assert chosen is expires_soon


def test_the_fecha_limite_day_itself_is_usable():
    """Defect it catches: an off-by-one on Art. 62 blocks issuance on
    the fecha límite's own calendar day.
    """
    range_ = _range(issue_deadline=_TODAY)
    assert select_range([range_], _TODAY) is range_


def test_the_day_after_the_fecha_limite_is_not_usable():
    """Defect it catches: Art. 62's deadline is treated as inclusive
    one day too many.
    """
    range_ = _range(issue_deadline=_TODAY - timedelta(days=1))
    with pytest.raises(CaiRangeExpired):
        select_range([range_], _TODAY)


def test_an_exhausted_current_range_falls_through_to_a_standby_one():
    """Defect it catches: a false "exhausted" error even though a
    pre-registered standby range is usable (the false-exhaustion trap
    AD-5 names, exercised here at the pure-selection level).
    """
    exhausted = _range(range_start=1, range_end=100, next_number=101)
    standby = _range(range_start=101, range_end=200, next_number=101)
    chosen = select_range([exhausted, standby], _TODAY)
    assert chosen is standby


def test_select_range_raises_missing_with_no_range_at_all():
    with pytest.raises(CaiRangeMissing):
        select_range([], _TODAY)


def test_select_range_raises_expired_when_a_range_still_has_numbers_but_is_past_its_deadline():
    """Defect it catches: an "exhausted" error reported for a range
    that is actually expired, which would point the workshop at the
    wrong fix (register a new range, versus nothing to do).
    """
    range_ = _range(issue_deadline=_TODAY - timedelta(days=1), next_number=50)
    with pytest.raises(CaiRangeExpired):
        select_range([range_], _TODAY)


def test_select_range_raises_exhausted_when_no_range_has_numbers_left():
    range_ = _range(range_end=100, next_number=101, issue_deadline=date(2027, 1, 1))
    with pytest.raises(CaiRangeExhausted):
        select_range([range_], _TODAY)


def test_overlaps_adjacent_ranges_do_not_overlap():
    """Defect it catches: valid, non-overlapping consecutive ranges
    (1-500, 501-1000) are incorrectly rejected.
    """
    first = _range(range_start=1, range_end=500)
    second = _range(range_start=501, range_end=1000)
    assert overlaps(second, [first]) is False


def test_overlaps_intersecting_ranges_overlap():
    """Defect it catches: an overlapping range is accepted, making a
    duplicate correlative possible.
    """
    first = _range(range_start=1, range_end=500)
    second = _range(range_start=400, range_end=900)
    assert overlaps(second, [first]) is True


def test_overlaps_a_different_document_type_never_collides():
    """Defect it catches: ranges of different document types are
    rejected as overlapping even though their numbering is
    independent.
    """
    first = _range(range_start=1, range_end=500, document_type=DocumentType.invoice)
    second = _range(range_start=1, range_end=500, document_type=DocumentType.credit_note)
    assert overlaps(second, [first]) is False


def test_overlaps_different_codes_never_collide():
    """Defect it catches: a range under a different establecimiento or
    punto de emisión is rejected as overlapping one it can never
    actually collide with.
    """
    first = _range(range_start=1, range_end=500, establishment_code="001")
    second = _range(range_start=1, range_end=500, establishment_code="002")
    assert overlaps(second, [first]) is False
