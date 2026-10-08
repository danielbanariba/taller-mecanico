"""The SAR document number value object (AD-12): assembled once from
the fiscal profile's codes and the allocated correlative. The codes and
the correlative are stored separately on each document; this value
object only owns the fixed printed format.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from taller.invoicing.domain.errors import InvalidCorrelative

MIN_CORRELATIVE: Final = 1
MAX_CORRELATIVE: Final = 99_999_999


class DocumentType(StrEnum):
    """A SAR document type code.

    Lowercase members, matching every other wire-value `StrEnum` in
    this codebase (`LineKind`, `PaymentMethod`, `WorkOrderStatus`); the
    wire value itself (``"01"``, ``"06"``) is what SAR, the database
    checks, and the API's `detail` codes actually compare.
    """

    invoice = "01"
    credit_note = "06"


@dataclass(frozen=True, slots=True)
class DocumentNumber:
    """``NNN-NNN-TT-NNNNNNNN`` (Art. 10-11): the profile's
    establecimiento and punto de emisión codes, the document type, and
    the allocated correlative zero-padded to 8 digits.
    """

    establishment: str
    emission_point: str
    document_type: DocumentType
    correlative: int

    def __post_init__(self) -> None:
        if not MIN_CORRELATIVE <= self.correlative <= MAX_CORRELATIVE:
            raise InvalidCorrelative(self.correlative)

    def __str__(self) -> str:
        return (
            f"{self.establishment}-{self.emission_point}-"
            f"{self.document_type.value}-{self.correlative:08d}"
        )
