"""SQLAlchemy ORM models for the fiscal invoicing feature.

Phase A: the fiscal profile, CAI ranges, and the Factura (`fiscal_invoices`
and `fiscal_invoice_lines`) tables. AD-10's shared snapshot columns are
factored into three small declarative mixins (``IssuerSnapshot``,
``CaiSnapshot``, ``Amounts``) instead of one shared ``fiscal_documents``
table, so phase B's `FiscalCreditNoteModel` can reuse the same column
definitions on its own table without duplicating them (AD-10's rejected
alternative 1).

The immutability triggers (`taller_fiscal_invoice_guard` on
`fiscal_invoices`, `taller_fiscal_append_only` on `fiscal_invoice_lines`)
are declared only in the migration: `alembic check` never compares
triggers, so they add no autogenerate drift (design.md's AD-10
"Rationale").
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from taller.shared.db import Base


class IssuerSnapshot:
    """Mixin: the issuer fields copied from `FiscalProfileModel` at
    issuance (AD-10), shared by `FiscalInvoiceModel` and, in phase B,
    `FiscalCreditNoteModel`.
    """

    issuer_rtn: Mapped[str] = mapped_column(String(14), nullable=False)
    issuer_legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer_trade_name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer_address: Mapped[str] = mapped_column(String(300), nullable=False)
    issuer_phone: Mapped[str] = mapped_column(String(8), nullable=False)
    issuer_email: Mapped[str] = mapped_column(String(254), nullable=False)


class CaiSnapshot:
    """Mixin: the CAI block copied from the allocated `CaiRangeModel` row
    at issuance (AD-10).
    """

    cai: Mapped[str] = mapped_column(String(50), nullable=False)
    range_first_number: Mapped[str] = mapped_column(String(19), nullable=False)
    range_last_number: Mapped[str] = mapped_column(String(19), nullable=False)
    issue_deadline: Mapped[date] = mapped_column(Date, nullable=False)


class Amounts:
    """Mixin: the gravado/ISV split common to every document type (AD-8).

    `FiscalInvoiceModel` adds its own `exempt_cents`, `exonerated_cents`,
    `discount_cents`, and `total_cents`; phase B's `FiscalCreditNoteModel`
    adds only its own `total_cents` on top of this mixin.
    """

    taxable_15_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    isv_15_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)


class FiscalProfileModel(Base):
    """A workshop's fiscal data (AD-3): one row per workshop, always
    complete once saved -- a workshop that never opts in has no row.
    """

    __tablename__ = "fiscal_profiles"
    __table_args__ = (
        CheckConstraint("rtn ~ '^[0-9]{14}$'", name="ck_fiscal_profiles_rtn_digits"),
        CheckConstraint(
            "establishment_code ~ '^[0-9]{3}$'", name="ck_fiscal_profiles_establishment_code"
        ),
        CheckConstraint(
            "emission_point_code ~ '^[0-9]{3}$'", name="ck_fiscal_profiles_emission_point_code"
        ),
    )

    workshop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workshops.id"), primary_key=True)
    rtn: Mapped[str] = mapped_column(String(14), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    trade_name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    phone: Mapped[str] = mapped_column(String(8), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    establishment_code: Mapped[str] = mapped_column(String(3), nullable=False)
    emission_point_code: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CaiRangeModel(Base):
    """One CAI authorization: a bounded, self-numbering counter row
    (AD-4). `document_type` allows `06` from phase A on so phase B needs
    no constraint change; the API itself rejects `06` until phase B
    (`unsupported_document_type`).
    """

    __tablename__ = "cai_ranges"
    __table_args__ = (
        CheckConstraint("document_type IN ('01', '06')", name="ck_cai_ranges_document_type"),
        CheckConstraint(
            "range_start >= 1 AND range_start <= range_end AND range_end <= 99999999",
            name="ck_cai_ranges_bounds",
        ),
        CheckConstraint(
            "next_number >= range_start AND next_number <= range_end + 1",
            name="ck_cai_ranges_next_number",
        ),
        Index("ix_cai_ranges_workshop_id_document_type", "workshop_id", "document_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workshops.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(2), nullable=False)
    cai: Mapped[str] = mapped_column(String(50), nullable=False)
    establishment_code: Mapped[str] = mapped_column(String(3), nullable=False)
    emission_point_code: Mapped[str] = mapped_column(String(3), nullable=False)
    range_start: Mapped[int] = mapped_column(Integer, nullable=False)
    range_end: Mapped[int] = mapped_column(Integer, nullable=False)
    next_number: Mapped[int] = mapped_column(Integer, nullable=False)
    issue_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FiscalInvoiceModel(Base, IssuerSnapshot, CaiSnapshot, Amounts):
    """An issued Factura: an immutable snapshot of everything SAR
    requires on the document (AD-10), guarded at the database level by
    the `taller_fiscal_invoice_guard` trigger (declared in the
    migration).
    """

    __tablename__ = "fiscal_invoices"
    __table_args__ = (
        CheckConstraint("issue_date <= issue_deadline", name="ck_fiscal_invoices_within_deadline"),
        CheckConstraint(
            "buyer_rtn IS NULL OR buyer_name IS NOT NULL", name="ck_fiscal_invoices_buyer_pair"
        ),
        CheckConstraint(
            "total_cents < 1000000 OR (buyer_name IS NOT NULL AND buyer_rtn IS NOT NULL)",
            name="ck_fiscal_invoices_identified_from_10000",
        ),
        CheckConstraint("exempt_cents >= 0", name="ck_fiscal_invoices_exempt_nonneg"),
        CheckConstraint("exonerated_cents >= 0", name="ck_fiscal_invoices_exonerated_nonneg"),
        CheckConstraint("discount_cents >= 0", name="ck_fiscal_invoices_discount_nonneg"),
        CheckConstraint(
            "exempt_cents + exonerated_cents + taxable_15_cents + isv_15_cents = total_cents",
            name="ck_fiscal_invoices_breakdown_sum",
        ),
        CheckConstraint("total_cents > 0", name="ck_fiscal_invoices_total_positive"),
        UniqueConstraint(
            "cai_range_id", "correlative", name="uq_fiscal_invoices_range_correlative"
        ),
        UniqueConstraint("workshop_id", "number", name="uq_fiscal_invoices_workshop_number"),
        Index(
            "uq_fiscal_invoices_order_active",
            "order_id",
            unique=True,
            postgresql_where=text("credited_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workshops.id"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("work_orders.id"), nullable=False, index=True
    )
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    cai_range_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cai_ranges.id"), nullable=False)
    correlative: Mapped[int] = mapped_column(Integer, nullable=False)
    number: Mapped[str] = mapped_column(String(19), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    buyer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    buyer_rtn: Mapped[str | None] = mapped_column(String(14), nullable=True)
    exempt_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exonerated_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    discount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_in_words: Mapped[str] = mapped_column(String(300), nullable=False)
    credited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FiscalInvoiceLineModel(Base):
    """One line of an issued Factura, copied from the order's non-removed
    lines at issuance. Append-only, guarded by
    `taller_fiscal_append_only` (declared in the migration).
    """

    __tablename__ = "fiscal_invoice_lines"
    __table_args__ = (
        CheckConstraint(
            "line_total_cents = quantity::bigint * unit_price_cents",
            name="ck_fiscal_invoice_lines_total",
        ),
        UniqueConstraint("invoice_id", "position", name="uq_fiscal_invoice_lines_invoice_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workshops.id"), nullable=False, index=True
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fiscal_invoices.id"), nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    source_line_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("work_order_lines.id"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)


class FiscalCreditNoteModel(Base, IssuerSnapshot, CaiSnapshot, Amounts):
    """A Nota de Credito (phase B, AD-13): a full-amount, immutable
    snapshot crediting a Factura, guarded at the database level by the
    `taller_fiscal_append_only` trigger (declared in the migration,
    reusing the function `db3dfe52854a` created for
    `fiscal_invoice_lines`).
    """

    __tablename__ = "fiscal_credit_notes"
    __table_args__ = (
        CheckConstraint(
            "issue_date <= issue_deadline", name="ck_fiscal_credit_notes_within_deadline"
        ),
        CheckConstraint("length(btrim(reason)) > 0", name="ck_fiscal_credit_notes_reason_nonempty"),
        CheckConstraint(
            "taxable_15_cents + isv_15_cents = total_cents",
            name="ck_fiscal_credit_notes_breakdown_sum",
        ),
        UniqueConstraint("invoice_id", name="uq_fiscal_credit_notes_invoice_id"),
        UniqueConstraint(
            "cai_range_id", "correlative", name="uq_fiscal_credit_notes_range_correlative"
        ),
        UniqueConstraint("workshop_id", "number", name="uq_fiscal_credit_notes_workshop_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    workshop_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workshops.id"), nullable=False)
    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fiscal_invoices.id"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("work_orders.id"), nullable=False, index=True
    )
    cai_range_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cai_ranges.id"), nullable=False)
    correlative: Mapped[int] = mapped_column(Integer, nullable=False)
    number: Mapped[str] = mapped_column(String(19), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    buyer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    buyer_rtn: Mapped[str | None] = mapped_column(String(14), nullable=True)
    original_cai: Mapped[str] = mapped_column(String(50), nullable=False)
    original_number: Mapped[str] = mapped_column(String(19), nullable=False)
    original_issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(300), nullable=False)
    total_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_in_words: Mapped[str] = mapped_column(String(300), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
