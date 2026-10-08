"""Tests for the SAR document number format (AD-12).

Defect it catches: an unpadded or misordered number printed on a legal
document (`fiscal-invoices`, "A number is assembled from the profile
and the allocated correlative").
"""

import pytest

from taller.invoicing.domain.document_number import DocumentNumber, DocumentType
from taller.invoicing.domain.errors import InvalidCorrelative


def test_a_number_is_assembled_from_the_profile_and_the_allocated_correlative():
    number = DocumentNumber(
        establishment="001",
        emission_point="001",
        document_type=DocumentType.invoice,
        correlative=1,
    )
    assert str(number) == "001-001-01-00000001"


def test_the_maximum_correlative_keeps_eight_digits():
    number = DocumentNumber(
        establishment="001",
        emission_point="001",
        document_type=DocumentType.invoice,
        correlative=99_999_999,
    )
    assert str(number) == "001-001-01-99999999"


def test_a_credit_note_number_uses_its_own_type_code():
    number = DocumentNumber(
        establishment="001",
        emission_point="001",
        document_type=DocumentType.credit_note,
        correlative=1,
    )
    assert str(number) == "001-001-06-00000001"


@pytest.mark.parametrize("correlative", [0, -1, 100_000_000])
def test_an_out_of_bounds_correlative_raises(correlative):
    with pytest.raises(InvalidCorrelative):
        DocumentNumber(
            establishment="001",
            emission_point="001",
            document_type=DocumentType.invoice,
            correlative=correlative,
        )
