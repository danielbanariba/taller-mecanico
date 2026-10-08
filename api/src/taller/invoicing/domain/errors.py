"""Domain errors for the invoicing feature (fiscal profile, CAI ranges,
Facturas, and -- in phase B -- Notas de Crédito).
"""


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
