"""Honduran phone number value object.

Honduran mobile and landline numbers are 8 digits, with the first digit
between 2 and 9 (0 and 1 are never issued as a first digit). Users commonly
type the number with spaces or dashes, and sometimes include the country
code (+504 or 504), so all of those forms normalize to the same 8 digits.
"""

import re
from dataclasses import dataclass

from taller.identity.domain.errors import InvalidPhoneNumber

_LOCAL_NUMBER_PATTERN = re.compile(r"^\d{8}$")
_SEPARATOR_PATTERN = re.compile(r"[\s-]")
_FIRST_DIGITS = "23456789"


@dataclass(frozen=True, slots=True)
class PhoneNumber:
    """An 8-digit Honduran phone number, already normalized."""

    value: str

    def __post_init__(self) -> None:
        if not _LOCAL_NUMBER_PATTERN.fullmatch(self.value) or self.value[0] not in _FIRST_DIGITS:
            raise InvalidPhoneNumber(self.value)

    @classmethod
    def from_raw(cls, raw: str) -> "PhoneNumber":
        """Normalize free-form user input into a validated :class:`PhoneNumber`.

        Strips spaces and dashes, then strips a leading ``+504`` or ``504``
        country-code prefix, before validating the remaining 8 digits.
        """
        if not isinstance(raw, str):
            raise InvalidPhoneNumber(str(raw))

        cleaned = _SEPARATOR_PATTERN.sub("", raw.strip())
        if cleaned.startswith("+504"):
            cleaned = cleaned[4:]
        elif len(cleaned) == 11 and cleaned.startswith("504"):
            cleaned = cleaned[3:]

        try:
            return cls(cleaned)
        except InvalidPhoneNumber:
            # Re-raise carrying the original input, which is more useful in
            # an error message than the partially-cleaned value.
            raise InvalidPhoneNumber(raw) from None
