"""Item name normalization: trims whitespace and enforces length bounds.

Mirrors ``taller.identity.domain.phone_number``: a value, not a formatted
string, is the unit of validation, so both the HTTP schema layer and the
application layer share one source of truth for what a valid item name is.
"""

from taller.inventory.domain.errors import InvalidItemName

#: Matches the HTTP contract: item names are 1-120 characters after trimming.
MAX_NAME_LENGTH = 120


def normalize_item_name(raw: str) -> str:
    """Trim ``raw`` and validate it is a non-empty name within length bounds.

    Raises:
        InvalidItemName: the trimmed value is empty or longer than
            :data:`MAX_NAME_LENGTH` characters.
    """
    if not isinstance(raw, str):
        raise InvalidItemName(str(raw))

    trimmed = raw.strip()
    if not trimmed or len(trimmed) > MAX_NAME_LENGTH:
        raise InvalidItemName(raw)
    return trimmed
