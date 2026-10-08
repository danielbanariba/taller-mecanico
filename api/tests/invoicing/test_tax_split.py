"""Tests for the ISV split (AD-8): gravado and ISV always add up to a
document's total exactly, in integer cents, with no float anywhere.
"""

import random
from fractions import Fraction

from taller.invoicing.domain.tax import split_tax_inclusive_total


def test_every_total_in_a_dense_range_splits_exactly():
    """Defect it catches: float division or a rounding bug that lets
    gravado plus ISV drift away from the total for some totals.
    """
    for total_cents in range(0, 200_001):
        amounts = split_tax_inclusive_total(total_cents)
        assert amounts.taxable_15_cents + amounts.isv_15_cents == total_cents


def test_many_random_large_totals_split_exactly():
    """Defect it catches: an overflow or rounding bug that only shows
    up for totals far beyond typical invoice sizes.
    """
    rng = random.Random(20261008)
    for _ in range(10_000):
        total_cents = rng.randint(0, 10**14)
        amounts = split_tax_inclusive_total(total_cents)
        assert amounts.taxable_15_cents + amounts.isv_15_cents == total_cents


def test_taxable_matches_the_nearest_integer_to_100_over_115_of_the_total():
    """Independent oracle via `Fraction`, not the formula under test.

    Defect it catches: a rounding-direction bug -- for example
    computing ISV forward as 15% of the base, which overshoots the
    total by one cent at T = 100000 (AD-8's worked example) -- and the
    ISV amount drifting more than a cent from a straight 15% of the
    base.
    """
    rng = random.Random(20261009)
    totals = [*range(0, 2_000, 7), *(rng.randint(0, 10**12) for _ in range(500))]
    for total_cents in totals:
        amounts = split_tax_inclusive_total(total_cents)
        assert amounts.taxable_15_cents == round(Fraction(total_cents * 100, 115))
        forward_isv = Fraction(15, 100) * amounts.taxable_15_cents
        assert abs(amounts.isv_15_cents - forward_isv) <= 1


def test_a_clean_total_splits_to_the_documented_values():
    """Defect it catches: the AD-8 worked example regresses (an L
    1,150.00 total no longer splits into L 1,000.00 gravado and L
    150.00 ISV, the `fiscal-invoices` spec's "A clean total splits
    exactly" scenario).
    """
    amounts = split_tax_inclusive_total(115_000)
    assert (amounts.taxable_15_cents, amounts.isv_15_cents) == (100_000, 15_000)


def test_a_non_evenly_divisible_total_splits_to_the_documented_values():
    """Defect it catches: the AD-8 worked example for a total that
    does not divide evenly by 1.15 regresses (L 1,000.00 -> L 869.57
    gravado / L 130.43 ISV, not the one-cent-over forward calculation
    AD-8 explicitly rejects).
    """
    amounts = split_tax_inclusive_total(100_000)
    assert (amounts.taxable_15_cents, amounts.isv_15_cents) == (86_957, 13_043)
