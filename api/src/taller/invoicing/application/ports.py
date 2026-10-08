"""Ports the invoicing use cases depend on, implemented by adapters."""

import uuid
from datetime import datetime
from typing import Protocol

from taller.invoicing.domain.document_number import DocumentType
from taller.invoicing.domain.documents import FiscalCreditNote, FiscalInvoice
from taller.invoicing.domain.profile import FiscalProfile
from taller.invoicing.domain.ranges import CaiRange


class FiscalProfileRepository(Protocol):
    def get(self, *, workshop_id: uuid.UUID) -> FiscalProfile | None: ...

    def get_for_update(self, *, workshop_id: uuid.UUID) -> FiscalProfile | None:
        """Like :meth:`get`, but locks the row (``SELECT ... FOR
        UPDATE``) -- the per-workshop fiscal mutex every other
        invoicing write also takes (AD-5).
        """
        ...

    def add(self, profile: FiscalProfile) -> None: ...

    def save(self, profile: FiscalProfile) -> None:
        """Persist every mutable field of an already-existing profile."""
        ...


class CaiRangeRepository(Protocol):
    def list(
        self, *, workshop_id: uuid.UUID, document_type: DocumentType | None = None
    ) -> list[CaiRange]: ...

    def get_by_id(self, *, workshop_id: uuid.UUID, range_id: uuid.UUID) -> CaiRange | None: ...

    def add(self, cai_range: CaiRange) -> None: ...

    def save(self, cai_range: CaiRange) -> None:
        """Persist every field of an already-existing, not-yet-used
        range after a correction (`update_range` never reaches this
        with an in-use range). `allocate` is the only path that
        advances `next_number` for a range already in use.
        """
        ...

    def allocate(self, *, range_id: uuid.UUID, now: datetime) -> int | None:
        """Lock-free, single-statement allocation (AD-5):
        ``UPDATE ... SET next_number = next_number + 1 WHERE
        next_number <= range_end RETURNING next_number - 1``. Returns
        ``None`` when the range is already exhausted. The caller holds
        the workshop's fiscal profile lock, which serializes this
        against every other fiscal write for the same workshop.
        """
        ...


class FiscalInvoiceRepository(Protocol):
    def get_by_id(
        self, *, workshop_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> FiscalInvoice | None: ...

    def get_for_update(
        self, *, workshop_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> FiscalInvoice | None:
        """Like :meth:`get_by_id`, but locks the row (``SELECT ... FOR
        UPDATE``) -- the Factura lock a credit note takes right after
        the order lock, before deciding whether it is already credited
        (phase B, AD-13's lock order).
        """
        ...

    def has_active_for_order(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> bool:
        """Whether the order has a non-credited Factura right now
        (`uq_fiscal_invoices_order_active`'s partial index backs this
        at the database level too).
        """
        ...

    def list_for_order(self, *, workshop_id: uuid.UUID, order_id: uuid.UUID) -> list[FiscalInvoice]:
        """Newest first, credited ones included."""
        ...

    def add(self, invoice: FiscalInvoice) -> None:
        """Persist a brand-new, immutable invoice together with its lines."""
        ...

    def mark_credited(self, *, invoice_id: uuid.UUID, credited_at: datetime) -> None:
        """Stamp the one column the AD-10 trigger ever lets change after
        insert (phase B): the caller must already hold this row's lock
        via :meth:`get_for_update`.
        """
        ...


class CreditNoteRepository(Protocol):
    """Phase B (AD-13)."""

    def get_by_id(
        self, *, workshop_id: uuid.UUID, credit_note_id: uuid.UUID
    ) -> FiscalCreditNote | None: ...

    def get_for_invoice(
        self, *, workshop_id: uuid.UUID, invoice_id: uuid.UUID
    ) -> FiscalCreditNote | None:
        """The credit note crediting this invoice, if one was issued
        (`uq_fiscal_credit_notes_invoice_id` backs this at the database
        level too): used to report `credit_note` on a Factura's response.
        """
        ...

    def add(self, credit_note: FiscalCreditNote) -> None:
        """Persist a brand-new, immutable, append-only credit note."""
        ...
