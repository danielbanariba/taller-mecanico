"""Tests for buyer rules at issuance (AD-11)."""

import pytest

from taller.invoicing.domain.buyer import Buyer, resolve_buyer
from taller.invoicing.domain.errors import BuyerIdentificationRequired, BuyerNameRequired


def test_no_name_and_no_rtn_resolves_to_consumidor_final():
    """Defect it catches: a buyer with no supplied data ends up with a
    stray name or RTN instead of plain "CONSUMIDOR FINAL".
    """
    assert resolve_buyer(name=None, rtn=None, total_cents=1) == Buyer(name=None, rtn=None)


def test_a_name_alone_resolves_to_a_named_consumidor_final():
    buyer = resolve_buyer(name="Juan Perez", rtn=None, total_cents=1)
    assert buyer == Buyer(name="Juan Perez", rtn=None)


def test_a_name_and_rtn_resolve_to_an_identified_buyer():
    buyer = resolve_buyer(name="Juan Perez", rtn="08011990123456", total_cents=1)
    assert buyer == Buyer(name="Juan Perez", rtn="08011990123456")


def test_an_rtn_alone_is_rejected():
    """Defect it catches: an RTN prints on a document with no name
    attached to it (AD-11).
    """
    with pytest.raises(BuyerNameRequired):
        resolve_buyer(name=None, rtn="08011990123456", total_cents=1)


def test_just_below_the_threshold_needs_no_identification():
    """Defect it catches: the L 10,000 boundary is off by one on the
    low side, blocking a consumidor final invoice that should pass.
    """
    resolve_buyer(name=None, rtn=None, total_cents=999_999)


def test_at_the_threshold_without_identification_is_rejected():
    """Defect it catches: the L 10,000 boundary is off by one on the
    high side, letting an unidentified consumidor final through.
    """
    with pytest.raises(BuyerIdentificationRequired):
        resolve_buyer(name=None, rtn=None, total_cents=1_000_000)


def test_at_the_threshold_with_identification_succeeds():
    buyer = resolve_buyer(name="Juan Perez", rtn="08011990123456", total_cents=1_000_000)
    assert buyer == Buyer(name="Juan Perez", rtn="08011990123456")
