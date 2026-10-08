"""Domain errors for the invoicing feature (fiscal profile, CAI ranges,
Facturas, and -- in phase B -- Notas de Crédito).
"""

import uuid
from datetime import date


class InvalidCorrelative(ValueError):
    """Raised when a document number's correlative is outside
    1..99,999,999 (Art. 10-11).
    """

    def __init__(self, correlative: int) -> None:
        super().__init__(f"Invalid correlative: {correlative!r}")
        self.correlative = correlative


class AmountInWordsOutOfRange(ValueError):
    """Raised when an amount cannot be rendered in words: negative, or
    its lempira part exceeds `amount_in_words.MAX_LEMPIRAS` (AD-9).
    """

    def __init__(self, total_cents: int) -> None:
        super().__init__(f"Amount out of range for words: {total_cents!r}")
        self.total_cents = total_cents


class BuyerNameRequired(Exception):
    """Raised when an RTN is supplied with no billing name (AD-11): an
    RTN alone can never identify a buyer.
    """


class BuyerIdentificationRequired(Exception):
    """Raised when a document's total is at or above the L 10,000.00
    identification threshold and either the buyer's name or RTN is
    missing (AD-11).
    """


class CaiRangeMissing(Exception):
    """Raised when no CAI range of the needed document type exists at
    all (AD-6).
    """


class CaiRangeExpired(Exception):
    """Raised when no CAI range is usable today, but at least one
    still has numbers left -- so every one of those is past its fecha
    límite (AD-4, AD-6).
    """


class CaiRangeExhausted(Exception):
    """Raised when no CAI range is usable today and none has numbers
    left either (AD-4, AD-6).
    """


class FiscalProfileMissing(Exception):
    """Raised when an action needs a fiscal profile and the workshop
    has none (AD-3).
    """


class FiscalProfileCodesLocked(Exception):
    """Raised when an edit would change the establecimiento or punto
    de emisión code while any CAI range is still usable today (AD-3):
    a CAI is granted per punto de emisión, so changing either code
    would invalidate every number still available on that range.
    """

    def __init__(self, workshop_id: uuid.UUID) -> None:
        super().__init__(f"Fiscal profile codes are locked: {workshop_id}")
        self.workshop_id = workshop_id


class InvalidEmail(ValueError):
    """Raised when a value cannot be normalized into a valid email
    address (AD-3).
    """

    def __init__(self, raw: str) -> None:
        super().__init__(f"Invalid email: {raw!r}")
        self.raw = raw


class InvalidEstablishmentCode(ValueError):
    """Raised when a value is not exactly 3 digits (AD-3)."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"Invalid establishment code: {raw!r}")
        self.raw = raw


class InvalidEmissionPointCode(ValueError):
    """Raised when a value is not exactly 3 digits (AD-3)."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"Invalid emission point code: {raw!r}")
        self.raw = raw


class UnsupportedDocumentType(Exception):
    """Raised when a document type is not yet accepted: `06` before
    Phase B (AD-4). The database check already allows both from Phase
    A on, so this is purely an application-level gate.
    """

    def __init__(self, document_type: str) -> None:
        super().__init__(f"Unsupported document type: {document_type!r}")
        self.document_type = document_type


class InvalidCai(ValueError):
    """Raised when a CAI string, after normalization, fails the loose
    shape check (AD-4): SAR's exact format is unconfirmed (design's
    Open Questions), so only character set and length are enforced.
    """

    def __init__(self, raw: str) -> None:
        super().__init__(f"Invalid CAI: {raw!r}")
        self.raw = raw


class InvalidCaiRange(ValueError):
    """Raised when a range's bounds fail `1 <= range_start <=
    range_end <= 99,999,999` (AD-4).
    """

    def __init__(self, *, range_start: int, range_end: int) -> None:
        super().__init__(f"Invalid CAI range bounds: {range_start}-{range_end}")
        self.range_start = range_start
        self.range_end = range_end


class CaiDeadlinePassed(ValueError):
    """Raised when a fecha límite is already in the past (AD-4)."""

    def __init__(self, issue_deadline: date) -> None:
        super().__init__(f"CAI deadline already passed: {issue_deadline}")
        self.issue_deadline = issue_deadline


class CaiDeadlineTooFar(ValueError):
    """Raised when a fecha límite is more than 366 days out (AD-4): a
    CAI is valid for at most one year (Art. 62), so a deadline further
    away can only be a typo.
    """

    def __init__(self, issue_deadline: date) -> None:
        super().__init__(f"CAI deadline too far in the future: {issue_deadline}")
        self.issue_deadline = issue_deadline


class CaiRangeIdConflict(Exception):
    """Raised when a client-supplied range id exists with different fields."""

    def __init__(self, range_id: uuid.UUID) -> None:
        super().__init__(f"CAI range id already exists with different fields: {range_id}")
        self.range_id = range_id


class CaiRangeOverlap(Exception):
    """Raised when a range's bounds intersect another range of the
    same workshop, document type, establecimiento and punto de
    emisión (AD-4).
    """

    def __init__(self, range_id: uuid.UUID) -> None:
        super().__init__(f"CAI range overlaps an existing one: {range_id}")
        self.range_id = range_id


class CaiRangeImmutable(Exception):
    """Raised when editing a range from which at least one number has
    already been allocated (AD-4).
    """

    def __init__(self, range_id: uuid.UUID) -> None:
        super().__init__(f"CAI range is immutable once in use: {range_id}")
        self.range_id = range_id


class CaiRangeNotFound(Exception):
    """Raised when a range id does not exist in the caller's workshop.

    Also used when the range exists but belongs to another workshop,
    so tenant isolation never leaks whether the range exists at all.
    """

    def __init__(self, range_id: uuid.UUID) -> None:
        super().__init__(f"CAI range not found: {range_id}")
        self.range_id = range_id
