"""Vehicle plate normalization: strip, uppercase, drop separators (AD-9).

Mirrors ``taller.inventory.domain.item_name``: a value, not a formatted
string, is the unit of validation, so both the HTTP schema layer and the
application layer share one source of truth for what a valid plate is.
"""

import re

from taller.customers.domain.errors import InvalidPlate

#: A normalized plate is 1-12 uppercase letters and digits only.
_VALID_PLATE = re.compile(r"^[A-Z0-9]{1,12}$")

#: Whitespace (anywhere in the string) and the separators a plate is
#: commonly written with. Stripped before the result is validated.
_SEPARATORS = re.compile(r"[\s\-./]")


def normalize_plate(raw: str | None) -> str | None:
    """Normalize a raw plate string, or return ``None`` for an absent plate.

    ``raw`` is stripped, uppercased, and has every whitespace character and
    ``-``/``.``/``/`` removed. A result that normalizes to the empty string
    (``None``, or a plate made only of whitespace/separators) means "no
    plate" and is always allowed.

    Raises:
        InvalidPlate: the normalized, non-empty result contains a
            character other than an uppercase letter or digit, or is
            longer than 12 characters.
    """
    if raw is None:
        return None
    cleaned = _SEPARATORS.sub("", raw.strip().upper())
    if not cleaned:
        return None
    if not _VALID_PLATE.match(cleaned):
        raise InvalidPlate(raw)
    return cleaned
