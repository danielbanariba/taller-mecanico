"""Buyer rules at issuance (AD-11): CONSUMIDOR FINAL by default, named
or identified when buyer data is supplied, and mandatory
identification from L 10,000.00 including ISV.
"""

from dataclasses import dataclass
from typing import Final

from taller.invoicing.domain.errors import BuyerIdentificationRequired, BuyerNameRequired

#: L 10,000.00, tax-inclusive (Art. 10-11; the `fiscal-invoices` spec).
IDENTIFICATION_THRESHOLD_CENTS: Final = 1_000_000


@dataclass(frozen=True, slots=True)
class Buyer:
    """The buyer as stored on a document snapshot.

    Both ``None`` means "CONSUMIDOR FINAL" -- the legend itself is
    rendered by the print layer (``copy.ts``, AD-14), never stored
    here.
    """

    name: str | None
    rtn: str | None


def resolve_buyer(*, name: str | None, rtn: str | None, total_cents: int) -> Buyer:
    """Validate and resolve the buyer for a Factura or Nota de Crédito.

    Raises:
        BuyerNameRequired: ``rtn`` is supplied without a ``name``.
        BuyerIdentificationRequired: ``total_cents`` is at or above
            `IDENTIFICATION_THRESHOLD_CENTS` and either ``name`` or
            ``rtn`` is missing.
    """
    if rtn is not None and name is None:
        raise BuyerNameRequired()

    if total_cents >= IDENTIFICATION_THRESHOLD_CENTS and (name is None or rtn is None):
        raise BuyerIdentificationRequired()

    return Buyer(name=name, rtn=rtn)
