"""Tests for the Honduran RTN value object.

Defect this catches: a malformed RTN (the wrong digit count after
stripping separators) reaches a fiscal document instead of being
rejected before it is ever stored (`customers` delta, "An RTN with the
wrong digit count is rejected").
"""

import pytest

from taller.customers.domain.errors import InvalidRtn
from taller.customers.domain.rtn import Rtn


def test_strips_separators_and_keeps_the_fourteen_digits() -> None:
    assert Rtn.from_raw("0801-1990-123456") == "08011990123456"


@pytest.mark.parametrize(
    "raw",
    ["0801-1990-12345", "0801-1990-1234567"],
    ids=["thirteen_digits", "fifteen_digits"],
)
def test_rejects_a_result_that_is_not_fourteen_digits(raw: str) -> None:
    with pytest.raises(InvalidRtn):
        Rtn.from_raw(raw)
