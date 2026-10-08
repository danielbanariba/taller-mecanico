"""CAI range domain rules (AD-4): bounded correlative counters, their
derived state, and which usable range correlatives are allocated from
next.
"""

import re
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Final

from taller.invoicing.domain.document_number import DocumentType
from taller.invoicing.domain.errors import (
    CaiDeadlinePassed,
    CaiDeadlineTooFar,
    CaiRangeExhausted,
    CaiRangeExpired,
    CaiRangeMissing,
    InvalidCai,
    InvalidCaiRange,
)


class RangeState(StrEnum):
    """A range's state (AD-4): always derived from the row and today's
    date, never stored.
    """

    active = "active"
    standby = "standby"
    exhausted = "exhausted"
    expired = "expired"


@dataclass(slots=True)
class CaiRange:
    """One CAI authorization, as the domain sees it.

    Mirrors `taller.invoicing.adapters.models.CaiRangeModel`'s columns;
    the ORM row is mapped into this plain dataclass at the repository
    boundary, the same pattern every other feature in this codebase
    uses.
    """

    id: uuid.UUID
    workshop_id: uuid.UUID
    document_type: DocumentType
    cai: str
    establishment_code: str
    emission_point_code: str
    range_start: int
    range_end: int
    next_number: int
    issue_deadline: date
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    @property
    def remaining(self) -> int:
        """Numbers still available in this range."""
        return max(0, self.range_end - self.next_number + 1)

    @property
    def in_use(self) -> bool:
        """Whether at least one number has ever been allocated (AD-4's
        immutability rule: a used range can no longer be edited).
        """
        return self.next_number > self.range_start

    def usable_on(self, today: date) -> bool:
        """Whether this range could still allocate a number on
        ``today``: it has numbers left, and ``today`` is on or before
        its fecha límite (Art. 62, inclusive of that day).
        """
        return self.remaining > 0 and today <= self.issue_deadline


def _usable(ranges: Sequence[CaiRange], today: date) -> list[CaiRange]:
    return [r for r in ranges if r.usable_on(today)]


def _selection_key(range_: CaiRange) -> tuple[date, int, uuid.UUID]:
    return (range_.issue_deadline, range_.range_start, range_.id)


def select_range(ranges: Sequence[CaiRange], today: date) -> CaiRange:
    """The range correlatives are allocated from today (AD-4): among
    usable ranges, the earliest fecha límite first, then the lowest
    ``range_start``, then ``id``. Using the range that expires first
    wastes the fewest numbers, since Art. 62 voids whatever is left at
    the fecha límite.

    Raises:
        CaiRangeMissing: there is no range at all.
        CaiRangeExpired: no range is usable, but at least one still
            has numbers left (so every one of those is expired).
        CaiRangeExhausted: no range is usable, and none has numbers
            left either.
    """
    if not ranges:
        raise CaiRangeMissing()

    usable = _usable(ranges, today)
    if usable:
        return min(usable, key=_selection_key)

    if any(r.remaining > 0 for r in ranges):
        raise CaiRangeExpired()
    raise CaiRangeExhausted()


def range_states(ranges: Sequence[CaiRange], today: date) -> dict[uuid.UUID, RangeState]:
    """Every range's derived state (AD-4), including which single one
    is `active` among the usable ones.
    """
    usable = _usable(ranges, today)
    active_id = min(usable, key=_selection_key).id if usable else None

    states: dict[uuid.UUID, RangeState] = {}
    for r in ranges:
        if today > r.issue_deadline:
            states[r.id] = RangeState.expired
        elif r.remaining <= 0:
            states[r.id] = RangeState.exhausted
        elif r.id == active_id:
            states[r.id] = RangeState.active
        else:
            states[r.id] = RangeState.standby
    return states


def overlaps(candidate: CaiRange, others: Sequence[CaiRange]) -> bool:
    """Whether ``candidate``'s correlative interval intersects any
    range in ``others`` of the same document type, establecimiento and
    punto de emisión (AD-4).

    Adjacent ranges (``1-500`` and ``501-1000``) never overlap. A
    different document type or a different establecimiento/punto pair
    never collides either, since each is numbered independently.
    """
    return any(
        other.id != candidate.id
        and other.document_type == candidate.document_type
        and other.establishment_code == candidate.establishment_code
        and other.emission_point_code == candidate.emission_point_code
        and candidate.range_start <= other.range_end
        and other.range_start <= candidate.range_end
        for other in others
    )


#: A CAI is uppercased and stripped of whitespace, then must look like a
#: dash-separated run of alphanumerics (AD-4). SAR's exact format is
#: unconfirmed (design's Open Questions), so this is a loose shape check,
#: not the commonly seen 37-character grouping.
_CAI_PATTERN: Final = re.compile(r"^[0-9A-Z]+(-[0-9A-Z]+)*$")
MIN_CAI_LENGTH: Final = 10
MAX_CAI_LENGTH: Final = 50

#: `range_end` fits the fixed 8-digit correlative (AD-12).
MAX_RANGE_END: Final = 99_999_999

#: A CAI is valid for at most one year (Art. 62): a fecha límite further
#: out than this can only be a typo (AD-4).
MAX_DEADLINE_DAYS_AHEAD: Final = 366


def normalize_cai(raw: str) -> str:
    """Uppercase and strip every whitespace character from a CAI (AD-4).

    Raises:
        InvalidCai: the normalized value is not 10-50 characters of
            dash-separated alphanumerics.
    """
    cleaned = "".join(raw.split()).upper()
    if not (MIN_CAI_LENGTH <= len(cleaned) <= MAX_CAI_LENGTH) or not _CAI_PATTERN.fullmatch(
        cleaned
    ):
        raise InvalidCai(raw)
    return cleaned


def validate_range_bounds(*, range_start: int, range_end: int) -> None:
    """Raises: InvalidCaiRange: bounds fail `1 <= range_start <=
    range_end <= 99,999,999` (AD-4).
    """
    if not (1 <= range_start <= range_end <= MAX_RANGE_END):
        raise InvalidCaiRange(range_start=range_start, range_end=range_end)


def validate_issue_deadline(issue_deadline: date, *, today: date) -> None:
    """Raises:
    CaiDeadlinePassed: ``issue_deadline`` is already in the past.
    CaiDeadlineTooFar: ``issue_deadline`` is more than 366 days out.
    """
    if issue_deadline < today:
        raise CaiDeadlinePassed(issue_deadline)
    if issue_deadline > today + timedelta(days=MAX_DEADLINE_DAYS_AHEAD):
        raise CaiDeadlineTooFar(issue_deadline)


@dataclass(frozen=True, slots=True)
class RangeExpiresSoonWarning:
    """AD-18 (phase B): the latest usable range's fecha límite is
    within ``EXPIRY_WARNING_DAYS`` of today -- matching Art. 59's
    2-month window to request the next range.
    """

    days_left: int


@dataclass(frozen=True, slots=True)
class RangeLowNumbersWarning:
    """AD-18 (phase B): the usable ranges' remaining numbers, summed,
    are at or below ``LOW_NUMBERS_THRESHOLD``.
    """

    remaining: int


RangeWarning = RangeExpiresSoonWarning | RangeLowNumbersWarning

#: AD-18: an absolute count, not a percentage -- sensible at every
#: range size, where a percentage would warn too late on a small range
#: and months early on a large one (design.md's threshold rationale).
#: A named domain constant, not a setting, in v1.
LOW_NUMBERS_THRESHOLD: Final = 50

#: AD-18: matches Art. 59's 2-month window to request the next range.
EXPIRY_WARNING_DAYS: Final = 60


def range_warnings(ranges: Sequence[CaiRange], today: date) -> list[RangeWarning]:
    """Warnings for one document type's ranges (AD-18), evaluated over
    its *usable* ranges (``_usable``, the same set `select_range` and
    `range_states` consider active/standby): a warning means "act
    now", not "something will roll over" eventually, so a
    pre-registered standby range counts toward both checks and
    registering the next range silences both warnings before the
    current one lapses.
    """
    usable = _usable(ranges, today)
    if not usable:
        return []

    warnings: list[RangeWarning] = []

    days_left = (max(r.issue_deadline for r in usable) - today).days
    if days_left <= EXPIRY_WARNING_DAYS:
        warnings.append(RangeExpiresSoonWarning(days_left=days_left))

    remaining = sum(r.remaining for r in usable)
    if remaining <= LOW_NUMBERS_THRESHOLD:
        warnings.append(RangeLowNumbersWarning(remaining=remaining))

    return warnings
