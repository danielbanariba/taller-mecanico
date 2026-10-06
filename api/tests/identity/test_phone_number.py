"""Tests for the Honduran PhoneNumber value object.

Defects these catch:
- a normalizer that mangles digits instead of passing a well-formed local
  number through unchanged;
- a normalizer that doesn't strip the separators (spaces, dashes) or the
  country-code prefix (+504 / 504) that users commonly type on a phone,
  rejecting otherwise-valid numbers;
- missing length/charset/prefix validation that would let a malformed value
  (wrong length, a landline/mobile prefix Honduras never issues, or letters)
  reach the database as if it were a real phone number.
"""

import pytest

from taller.identity.domain.errors import InvalidPhoneNumber
from taller.identity.domain.phone_number import PhoneNumber


def test_accepts_plain_local_number() -> None:
    assert PhoneNumber.from_raw("99887766").value == "99887766"


@pytest.mark.parametrize(
    "raw",
    ["9988-7766", "9988 7766", " 99887766 ", "99-88-77-66"],
)
def test_normalizes_spaces_and_dashes_to_the_same_eight_digits(raw: str) -> None:
    assert PhoneNumber.from_raw(raw).value == "99887766"


@pytest.mark.parametrize(
    "raw",
    ["+504 9988-7766", "+50499887766", "504 9988 7766", "50499887766"],
)
def test_normalizes_country_code_prefix_to_the_same_eight_digits(raw: str) -> None:
    assert PhoneNumber.from_raw(raw).value == "99887766"


@pytest.mark.parametrize("raw", ["998877", "998877661", "+504998877"])
def test_rejects_wrong_length(raw: str) -> None:
    with pytest.raises(InvalidPhoneNumber):
        PhoneNumber.from_raw(raw)


@pytest.mark.parametrize("raw", ["09887766", "19887766"])
def test_rejects_leading_zero_or_one(raw: str) -> None:
    with pytest.raises(InvalidPhoneNumber):
        PhoneNumber.from_raw(raw)


def test_rejects_letters() -> None:
    with pytest.raises(InvalidPhoneNumber):
        PhoneNumber.from_raw("9988A766")
