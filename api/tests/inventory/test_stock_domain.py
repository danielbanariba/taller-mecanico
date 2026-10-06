"""Tests for the pure stock-delta arithmetic in `taller.inventory.domain.stock`.

Defects these catch:
- an `adjust` formula with its operands swapped (e.g. `current_stock -
  quantity` instead of `quantity - current_stock`), which would silently
  invert every physical-count correction;
- an `adjust` that clamps or rejects a negative starting stock instead of
  computing the real difference, hiding how much was actually counted in;
- `in`/`out` not actually flipping the sign, so a sale would increase stock
  instead of decreasing it (or vice versa);
- missing validation that lets a zero or negative quantity through for
  `in`/`out`, which would silently record a movement that changes nothing
  or corrupts the ledger;
- missing validation that lets a negative counted quantity through for
  `adjust`, which cannot represent a real physical count;
- missing validation that lets a quantity large enough to risk an integer
  overflow through for any movement kind.
"""

import pytest

from taller.inventory.domain.errors import InvalidMovementKind, InvalidMovementQuantity
from taller.inventory.domain.stock import MAX_QUANTITY, compute_delta


def test_in_adds_the_quantity() -> None:
    assert compute_delta(kind="in", quantity=5, current_stock=10) == 5


def test_out_subtracts_the_quantity() -> None:
    assert compute_delta(kind="out", quantity=5, current_stock=10) == -5


def test_adjust_to_a_lower_count_than_current_stock_is_negative() -> None:
    # Counted 7 while the ledger says 10: the correction is -3.
    assert compute_delta(kind="adjust", quantity=7, current_stock=10) == -3


def test_adjust_to_a_higher_count_from_negative_stock_is_positive() -> None:
    # Counted 12 while the ledger says -2: the correction is +14.
    assert compute_delta(kind="adjust", quantity=12, current_stock=-2) == 14


def test_adjust_to_the_same_count_is_a_zero_delta() -> None:
    assert compute_delta(kind="adjust", quantity=10, current_stock=10) == 0


@pytest.mark.parametrize("kind", ["in", "out"])
@pytest.mark.parametrize("quantity", [0, -1, -100])
def test_in_and_out_reject_non_positive_quantities(kind: str, quantity: int) -> None:
    with pytest.raises(InvalidMovementQuantity):
        compute_delta(kind=kind, quantity=quantity, current_stock=10)


def test_adjust_rejects_a_negative_counted_quantity() -> None:
    with pytest.raises(InvalidMovementQuantity):
        compute_delta(kind="adjust", quantity=-1, current_stock=10)


def test_unknown_kind_is_rejected() -> None:
    with pytest.raises(InvalidMovementKind):
        compute_delta(kind="transfer", quantity=5, current_stock=10)


@pytest.mark.parametrize("kind", ["in", "out"])
def test_in_and_out_reject_a_quantity_over_the_maximum(kind: str) -> None:
    with pytest.raises(InvalidMovementQuantity):
        compute_delta(kind=kind, quantity=MAX_QUANTITY + 1, current_stock=10)


def test_adjust_rejects_a_quantity_over_the_maximum() -> None:
    with pytest.raises(InvalidMovementQuantity):
        compute_delta(kind="adjust", quantity=MAX_QUANTITY + 1, current_stock=10)


def test_in_accepts_a_quantity_at_the_maximum() -> None:
    assert compute_delta(kind="in", quantity=MAX_QUANTITY, current_stock=0) == MAX_QUANTITY
