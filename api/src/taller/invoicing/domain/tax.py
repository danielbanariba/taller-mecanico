"""The ISV split (AD-8): one tarifa (15%), derived once from a
document's already tax-inclusive total (D1: line prices already
include ISV).
"""

from dataclasses import dataclass
from typing import Final

ISV_RATE_PERCENT: Final = 15
_BASE: Final = 100
_GROSS: Final = _BASE + ISV_RATE_PERCENT  # 115


@dataclass(frozen=True, slots=True)
class Amounts:
    """The gravado/ISV breakdown printed on a document (AD-8).

    ``exempt_cents``, ``exonerated_cents`` and ``discount_cents`` are
    always 0 in v1 (out of scope per the proposal); they default so
    every caller that only cares about the 15% split need not pass
    three zeros.
    """

    taxable_15_cents: int
    isv_15_cents: int
    exempt_cents: int = 0
    exonerated_cents: int = 0
    discount_cents: int = 0

    @property
    def total_cents(self) -> int:
        return self.exempt_cents + self.exonerated_cents + self.taxable_15_cents + self.isv_15_cents


def split_tax_inclusive_total(total_cents: int) -> Amounts:
    """Split a tax-inclusive total into its gravado 15% base and ISV.

    ``taxable_15_cents + isv_15_cents == total_cents`` holds by
    construction for every non-negative ``total_cents`` (AD-8): no tie
    is possible, because ``100/115 == 20/23`` and a fractional part of
    ``k/23`` is never exactly ``1/2``. Integer-only, no floats anywhere
    (archived AD-10).

    Raises:
        ValueError: ``total_cents`` is negative.
    """
    if total_cents < 0:
        raise ValueError(total_cents)
    taxable = (2 * _BASE * total_cents + _GROSS) // (2 * _GROSS)
    return Amounts(taxable_15_cents=taxable, isv_15_cents=total_cents - taxable)
