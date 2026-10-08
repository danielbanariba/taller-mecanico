"""Tests for CAI range warnings (phase B, AD-18): act-now signals that
a range is about to lapse or run low, evaluated over its usable
(active + standby) ranges.
"""

import uuid
from datetime import date, datetime, timedelta

from taller.invoicing.domain.document_number import DocumentType
from taller.invoicing.domain.ranges import (
    CaiRange,
    RangeExpiresSoonWarning,
    RangeLowNumbersWarning,
    range_warnings,
)

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


def test_no_fecha_limite_warning_appears_more_than_60_days_out():
    """Defect it catches: an off-by-one on Art. 59's 2-month window
    fires the warning one day too early.
    """
    range_ = _range(issue_deadline=_TODAY + timedelta(days=61))
    warnings = range_warnings([range_], _TODAY)
    assert warnings == []


def test_a_fecha_limite_warning_appears_exactly_60_days_before():
    """Defect it catches: an off-by-one on Art. 59's 2-month window
    misses the warning on the boundary day itself.
    """
    range_ = _range(issue_deadline=_TODAY + timedelta(days=60))
    warnings = range_warnings([range_], _TODAY)
    assert warnings == [RangeExpiresSoonWarning(days_left=60)]


def test_no_low_numbers_warning_appears_above_the_threshold():
    """Defect it catches: the low-numbers warning fires too early,
    training the owner to ignore it.
    """
    range_ = _range(range_start=1, range_end=100, next_number=49)
    warnings = range_warnings([range_], _TODAY)
    assert warnings == []


def test_a_low_numbers_warning_appears_at_the_threshold():
    """Defect it catches: an off-by-one on the design-fixed threshold
    (50) misses the warning right when the workshop still has time to
    act.
    """
    range_ = _range(range_start=1, range_end=100, next_number=51)
    warnings = range_warnings([range_], _TODAY)
    assert warnings == [RangeLowNumbersWarning(remaining=50)]


def test_a_standby_successor_silences_both_warnings():
    """Defect it catches: a warning still fires about a range a
    pre-registered standby successor already covers, training the
    owner to ignore every future warning.
    """
    about_to_lapse = _range(range_start=1, range_end=100, next_number=99, issue_deadline=_TODAY)
    standby = _range(
        range_start=101,
        range_end=600,
        next_number=101,
        issue_deadline=_TODAY + timedelta(days=300),
    )
    warnings = range_warnings([about_to_lapse, standby], _TODAY)
    assert warnings == []


def test_no_usable_range_produces_no_warning():
    """Defect it catches: an already-exhausted or expired range (which
    `cai_range_exhausted`/`cai_range_expired` already report through
    `blocked_reason`) also raises a stale warning, double-reporting
    the same problem under two different signals.
    """
    exhausted = _range(range_start=1, range_end=100, next_number=101)
    warnings = range_warnings([exhausted], _TODAY)
    assert warnings == []
