"""add fiscal credit notes table (Nota de Credito, phase B)

Revision ID: 952765f2fb33
Revises: 1a57ba6a8108
Create Date: 2026-10-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "952765f2fb33"
down_revision: str | Sequence[str] | None = "1a57ba6a8108"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Already created by `db3dfe52854a` for `fiscal_invoice_lines`; reused here
#: for `fiscal_credit_notes` (design.md's AD-10 "No other table changes").
_APPEND_ONLY_FUNCTION = "taller_fiscal_append_only"

#: AD-20: a downgrade over real credit notes is refused unless this exact
#: `-x` flag is passed, and then only on the disposable demo database (see
#: deploy/demo/README.md's rollback procedure).
_DISCARD_FLAG = "discard_fiscal_documents"
_DISCARD_FLAG_VALUE = "demo"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "fiscal_credit_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workshop_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("cai_range_id", sa.Uuid(), nullable=False),
        sa.Column("correlative", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=19), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("issuer_rtn", sa.String(length=14), nullable=False),
        sa.Column("issuer_legal_name", sa.String(length=200), nullable=False),
        sa.Column("issuer_trade_name", sa.String(length=200), nullable=False),
        sa.Column("issuer_address", sa.String(length=300), nullable=False),
        sa.Column("issuer_phone", sa.String(length=8), nullable=False),
        sa.Column("issuer_email", sa.String(length=254), nullable=False),
        sa.Column("cai", sa.String(length=50), nullable=False),
        sa.Column("range_first_number", sa.String(length=19), nullable=False),
        sa.Column("range_last_number", sa.String(length=19), nullable=False),
        sa.Column("issue_deadline", sa.Date(), nullable=False),
        sa.Column("buyer_name", sa.String(length=200), nullable=True),
        sa.Column("buyer_rtn", sa.String(length=14), nullable=True),
        sa.Column("original_cai", sa.String(length=50), nullable=False),
        sa.Column("original_number", sa.String(length=19), nullable=False),
        sa.Column("original_issue_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=300), nullable=False),
        sa.Column("taxable_15_cents", sa.BigInteger(), nullable=False),
        sa.Column("isv_15_cents", sa.BigInteger(), nullable=False),
        sa.Column("total_cents", sa.BigInteger(), nullable=False),
        sa.Column("total_in_words", sa.String(length=300), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "issue_date <= issue_deadline", name="ck_fiscal_credit_notes_within_deadline"
        ),
        sa.CheckConstraint(
            "length(btrim(reason)) > 0", name="ck_fiscal_credit_notes_reason_nonempty"
        ),
        sa.CheckConstraint(
            "taxable_15_cents + isv_15_cents = total_cents",
            name="ck_fiscal_credit_notes_breakdown_sum",
        ),
        sa.ForeignKeyConstraint(["cai_range_id"], ["cai_ranges.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["fiscal_invoices.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["work_orders.id"]),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_id", name="uq_fiscal_credit_notes_invoice_id"),
        sa.UniqueConstraint(
            "cai_range_id", "correlative", name="uq_fiscal_credit_notes_range_correlative"
        ),
        sa.UniqueConstraint("workshop_id", "number", name="uq_fiscal_credit_notes_workshop_number"),
    )
    op.create_index("ix_fiscal_credit_notes_order_id", "fiscal_credit_notes", ["order_id"])

    # Append-only trigger (AD-10): reuses the function `db3dfe52854a`
    # already created for `fiscal_invoice_lines`. `alembic check` never
    # compares triggers, so this adds no autogenerate drift.
    op.execute(
        f"CREATE TRIGGER {_APPEND_ONLY_FUNCTION} "
        "BEFORE UPDATE OR DELETE ON fiscal_credit_notes "
        f"FOR EACH ROW EXECUTE FUNCTION {_APPEND_ONLY_FUNCTION}()"
    )


def _guard_against_destroying_credit_notes() -> None:
    """AD-20: refuse to downgrade over real credit notes.

    Documents must be kept for custody (Art. 5, 41, 43); a bad release is
    reverted in code only. The one exception is the disposable public
    demo, which passes ``-x discard_fiscal_documents=demo`` after dumping
    the database first (see deploy/demo/README.md).
    """
    connection = op.get_bind()
    has_credit_notes = connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM fiscal_credit_notes)")
    ).scalar()
    if not has_credit_notes:
        return
    x_args = context.get_x_argument(as_dictionary=True)
    if x_args.get(_DISCARD_FLAG) != _DISCARD_FLAG_VALUE:
        raise RuntimeError(
            "Refusing to downgrade: fiscal_credit_notes holds documents that must be kept for "
            "custody (Art. 5, 41, 43). Re-run with "
            f"'-x {_DISCARD_FLAG}={_DISCARD_FLAG_VALUE}' only on the disposable demo database, "
            "after dumping it."
        )


def downgrade() -> None:
    """Downgrade schema."""
    _guard_against_destroying_credit_notes()

    # Only the trigger on fiscal_credit_notes is dropped: the
    # taller_fiscal_append_only() function itself is still used by
    # fiscal_invoice_lines (created in db3dfe52854a) and must survive a
    # phase-B-only downgrade.
    op.execute(f"DROP TRIGGER IF EXISTS {_APPEND_ONLY_FUNCTION} ON fiscal_credit_notes")

    op.drop_index("ix_fiscal_credit_notes_order_id", table_name="fiscal_credit_notes")
    op.drop_table("fiscal_credit_notes")
