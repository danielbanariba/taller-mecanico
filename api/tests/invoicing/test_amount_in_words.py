"""Tests for the total in words (AD-9): a small table-driven function
whose output appears, unchangeable, on every issued legal document.
"""

import pytest

from taller.invoicing.domain.amount_in_words import MAX_LEMPIRAS, amount_in_words
from taller.invoicing.domain.errors import AmountInWordsOutOfRange

#: (lempiras, cents, expected words). Each row is independently
#: derived from AD-9's wording rules, not read back from the
#: implementation under test.
_EXAMPLES = [
    (0, 50, "CERO LEMPIRAS CON 50/100"),
    (1, 0, "UN LEMPIRA CON 00/100"),
    (16, 0, "DIECISÉIS LEMPIRAS CON 00/100"),
    (21, 0, "VEINTIÚN LEMPIRAS CON 00/100"),
    (31, 0, "TREINTA Y UN LEMPIRAS CON 00/100"),
    (100, 0, "CIEN LEMPIRAS CON 00/100"),
    (101, 0, "CIENTO UN LEMPIRAS CON 00/100"),
    (115, 0, "CIENTO QUINCE LEMPIRAS CON 00/100"),
    (500, 0, "QUINIENTOS LEMPIRAS CON 00/100"),
    (700, 0, "SETECIENTOS LEMPIRAS CON 00/100"),
    (999, 0, "NOVECIENTOS NOVENTA Y NUEVE LEMPIRAS CON 00/100"),
    (1_000, 0, "UN MIL LEMPIRAS CON 00/100"),
    (1_150, 0, "UN MIL CIENTO CINCUENTA LEMPIRAS CON 00/100"),
    (21_000, 0, "VEINTIÚN MIL LEMPIRAS CON 00/100"),
    (101_000, 0, "CIENTO UN MIL LEMPIRAS CON 00/100"),
    (1_000_000, 0, "UN MILLÓN DE LEMPIRAS CON 00/100"),
    (2_021_001, 50, "DOS MILLONES VEINTIÚN MIL UN LEMPIRAS CON 50/100"),
    (
        MAX_LEMPIRAS,
        99,
        "NOVECIENTOS NOVENTA Y NUEVE MIL NOVECIENTOS NOVENTA Y NUEVE MILLONES "
        "NOVECIENTOS NOVENTA Y NUEVE MIL NOVECIENTOS NOVENTA Y NUEVE "
        "LEMPIRAS CON 99/100",
    ),
]


@pytest.mark.parametrize(("lempiras", "cents", "expected"), _EXAMPLES)
def test_amount_in_words_matches_the_ad9_example_table(lempiras, cents, expected):
    """Defect per row: a missing apocope (VEINTIUNO instead of
    VEINTIÚN), CIENTO printed for exactly 100, the singular LEMPIRA
    dropped, a missing DE after an exact million, lost accents, or a
    wrong recursion into the millions-of-millions range at the
    documented maximum.
    """
    assert amount_in_words(lempiras * 100 + cents) == expected


def test_above_the_maximum_raises():
    """Defect it catches: an amount beyond AD-9's documented bound is
    silently truncated or rendered as garbage instead of being
    rejected.
    """
    with pytest.raises(AmountInWordsOutOfRange):
        amount_in_words((MAX_LEMPIRAS + 1) * 100)


def test_a_negative_amount_raises():
    """Defect it catches: a negative total crashes with an unrelated
    error (a negative list index, an infinite loop) instead of a clear
    domain error.
    """
    with pytest.raises(AmountInWordsOutOfRange):
        amount_in_words(-1)
