"""Honduran RTN (Registro Tributario Nacional) value object.

Mirrors ``taller.customers.domain.plate``: a normalized value, not a
wrapper object, is the unit of validation, so both the HTTP schema layer
and `taller.invoicing` (which reuses this for the issuer and the buyer,
AD-1) share one source of truth for what a valid RTN is.
"""

import re

from taller.customers.domain.errors import InvalidRtn

#: Exactly 14 digits once separators are stripped (question 10: the
#: verified SAR research note gives no format; the market research
#: suggests 14 digits). No check-digit validation in v1.
_RTN_PATTERN = re.compile(r"^\d{14}$")

#: Whitespace and the separators an RTN is commonly typed with.
_SEPARATOR_PATTERN = re.compile(r"[\s-]")


class Rtn:
    """Namespace for normalizing a raw RTN into its stored form."""

    @staticmethod
    def from_raw(raw: str) -> str:
        """Normalize free-form user input into a validated 14-digit RTN.

        Strips spaces and dashes before validating the remaining digits.

        Raises:
            InvalidRtn: the normalized result is not exactly 14 digits.
        """
        cleaned = _SEPARATOR_PATTERN.sub("", raw.strip())
        if not _RTN_PATTERN.fullmatch(cleaned):
            raise InvalidRtn(raw)
        return cleaned
