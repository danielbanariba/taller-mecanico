"""Domain errors for the invoicing feature (fiscal profile, CAI ranges,
Facturas, and -- in phase B -- Notas de Crédito).
"""

import uuid


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
