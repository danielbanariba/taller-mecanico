"""Tests for `taller.inventory.domain.item_name.normalize_item_name`.

Defects these catch:
- a missing `.strip()` that lets a name of only whitespace through as
  "valid", producing an item with an effectively empty, unsearchable name;
- a missing or off-by-one length check that lets a name over 120 characters
  past validation, which would then fail at the database column instead of
  with a clear domain error.
"""

import pytest

from taller.inventory.domain.errors import InvalidItemName
from taller.inventory.domain.item_name import MAX_NAME_LENGTH, normalize_item_name


def test_trims_surrounding_whitespace() -> None:
    assert normalize_item_name("  Filtro de aceite  ") == "Filtro de aceite"


def test_rejects_a_blank_name() -> None:
    with pytest.raises(InvalidItemName):
        normalize_item_name("   ")


def test_accepts_a_name_at_the_maximum_length() -> None:
    name = "a" * MAX_NAME_LENGTH
    assert normalize_item_name(name) == name


def test_rejects_a_name_over_the_maximum_length() -> None:
    with pytest.raises(InvalidItemName):
        normalize_item_name("a" * (MAX_NAME_LENGTH + 1))
