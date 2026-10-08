"""The issued Factura (AD-10): an immutable snapshot of every printed
field, built once at issuance and never rendered from live data again.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime

#: Fixed namespace for every Factura line id, mirroring
#: `taller.workorders.domain.stock.WORK_ORDER_STOCK_NAMESPACE`: a pure
#: function of a constant input, identical across every process and run.
FISCAL_LINE_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL, "https://taller-mecanico.invalid/invoicing/fiscal-invoice-line"
)


def fiscal_invoice_line_id(invoice_id: uuid.UUID, position: int) -> uuid.UUID:
    """Deterministic line id (AD-10's data model): a replayed issuance
    resolves to the exact same line rows, never a duplicate set.
    """
    return uuid.uuid5(FISCAL_LINE_NAMESPACE, f"{invoice_id}:{position}")


@dataclass(frozen=True, slots=True)
class FiscalInvoiceLine:
    """One line of an issued Factura, copied from the order's
    non-removed lines at issuance (AD-10). Append-only: never edited
    after insert.
    """

    id: uuid.UUID
    position: int
    source_line_id: uuid.UUID
    kind: str
    description: str
    quantity: int
    unit_price_cents: int
    line_total_cents: int


@dataclass(slots=True)
class FiscalInvoice:
    """An issued Factura: an immutable snapshot of everything SAR
    requires on the document (AD-10). Mirrors
    `taller.invoicing.adapters.models.FiscalInvoiceModel`'s columns;
    the ORM row is mapped into this plain dataclass at the repository
    boundary, the same pattern every other feature in this codebase
    uses.
    """

    id: uuid.UUID
    workshop_id: uuid.UUID
    order_id: uuid.UUID
    order_number: int
    cai_range_id: uuid.UUID
    correlative: int
    number: str
    issued_at: datetime
    issue_date: date
    issuer_rtn: str
    issuer_legal_name: str
    issuer_trade_name: str
    issuer_address: str
    issuer_phone: str
    issuer_email: str
    cai: str
    range_first_number: str
    range_last_number: str
    issue_deadline: date
    buyer_name: str | None
    buyer_rtn: str | None
    exempt_cents: int
    exonerated_cents: int
    discount_cents: int
    taxable_15_cents: int
    isv_15_cents: int
    total_cents: int
    total_in_words: str
    credited_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    lines: list[FiscalInvoiceLine] = field(default_factory=list)
