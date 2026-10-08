"""add fiscal invoicing schema (fiscal profile, CAI ranges, Facturas) and
customer billing fields

Revision ID: db3dfe52854a
Revises: ffb1eb564de6
Create Date: 2026-10-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

# revision identifiers, used by Alembic.
revision: str = "db3dfe52854a"
down_revision: str | Sequence[str] | None = "ffb1eb564de6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Guards fiscal_invoices and fiscal_invoice_lines rows against UPDATE
#: (except the one-time credited_at stamp) and DELETE (design.md's AD-10,
#: Art. 5, 41, 43: an issued document is kept for custody, never rewritten
#: or deleted). Function names double as the trigger names below; Postgres
#: scopes trigger names per-table, so this is not a collision.
_INVOICE_GUARD_FUNCTION = "taller_fiscal_invoice_guard"
_APPEND_ONLY_FUNCTION = "taller_fiscal_append_only"

#: AD-20: a downgrade over real fiscal documents is refused unless this
#: exact `-x` flag is passed, and then only on the disposable demo
#: database (see deploy/demo/README.md's rollback procedure).
_DISCARD_FLAG = "discard_fiscal_documents"
_DISCARD_FLAG_VALUE = "demo"


def upgrade() -> None:
    """Upgrade schema."""
    # Customer billing fields (`sar-invoicing`'s `customers` delta):
    # metadata-only, both nullable with no default.
    op.add_column("customers", sa.Column("billing_name", sa.String(length=200), nullable=True))
    op.add_column("customers", sa.Column("rtn", sa.String(length=14), nullable=True))
    op.create_check_constraint(
        "ck_customers_rtn_digits", "customers", "rtn IS NULL OR rtn ~ '^[0-9]{14}$'"
    )

    op.create_table(
        "fiscal_profiles",
        sa.Column("workshop_id", sa.Uuid(), nullable=False),
        sa.Column("rtn", sa.String(length=14), nullable=False),
        sa.Column("legal_name", sa.String(length=200), nullable=False),
        sa.Column("trade_name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.String(length=300), nullable=False),
        sa.Column("phone", sa.String(length=8), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("establishment_code", sa.String(length=3), nullable=False),
        sa.Column("emission_point_code", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("rtn ~ '^[0-9]{14}$'", name="ck_fiscal_profiles_rtn_digits"),
        sa.CheckConstraint(
            "establishment_code ~ '^[0-9]{3}$'", name="ck_fiscal_profiles_establishment_code"
        ),
        sa.CheckConstraint(
            "emission_point_code ~ '^[0-9]{3}$'", name="ck_fiscal_profiles_emission_point_code"
        ),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"]),
        sa.PrimaryKeyConstraint("workshop_id"),
    )

    op.create_table(
        "cai_ranges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workshop_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=2), nullable=False),
        sa.Column("cai", sa.String(length=50), nullable=False),
        sa.Column("establishment_code", sa.String(length=3), nullable=False),
        sa.Column("emission_point_code", sa.String(length=3), nullable=False),
        sa.Column("range_start", sa.Integer(), nullable=False),
        sa.Column("range_end", sa.Integer(), nullable=False),
        sa.Column("next_number", sa.Integer(), nullable=False),
        sa.Column("issue_deadline", sa.Date(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("document_type IN ('01', '06')", name="ck_cai_ranges_document_type"),
        sa.CheckConstraint(
            "range_start >= 1 AND range_start <= range_end AND range_end <= 99999999",
            name="ck_cai_ranges_bounds",
        ),
        sa.CheckConstraint(
            "next_number >= range_start AND next_number <= range_end + 1",
            name="ck_cai_ranges_next_number",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cai_ranges_workshop_id_document_type", "cai_ranges", ["workshop_id", "document_type"]
    )

    op.create_table(
        "fiscal_invoices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workshop_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("order_number", sa.Integer(), nullable=False),
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
        sa.Column("exempt_cents", sa.BigInteger(), nullable=False),
        sa.Column("exonerated_cents", sa.BigInteger(), nullable=False),
        sa.Column("discount_cents", sa.BigInteger(), nullable=False),
        sa.Column("taxable_15_cents", sa.BigInteger(), nullable=False),
        sa.Column("isv_15_cents", sa.BigInteger(), nullable=False),
        sa.Column("total_cents", sa.BigInteger(), nullable=False),
        sa.Column("total_in_words", sa.String(length=300), nullable=False),
        sa.Column("credited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "issue_date <= issue_deadline", name="ck_fiscal_invoices_within_deadline"
        ),
        sa.CheckConstraint(
            "buyer_rtn IS NULL OR buyer_name IS NOT NULL", name="ck_fiscal_invoices_buyer_pair"
        ),
        sa.CheckConstraint(
            "total_cents < 1000000 OR (buyer_name IS NOT NULL AND buyer_rtn IS NOT NULL)",
            name="ck_fiscal_invoices_identified_from_10000",
        ),
        sa.CheckConstraint("exempt_cents >= 0", name="ck_fiscal_invoices_exempt_nonneg"),
        sa.CheckConstraint("exonerated_cents >= 0", name="ck_fiscal_invoices_exonerated_nonneg"),
        sa.CheckConstraint("discount_cents >= 0", name="ck_fiscal_invoices_discount_nonneg"),
        sa.CheckConstraint(
            "exempt_cents + exonerated_cents + taxable_15_cents + isv_15_cents = total_cents",
            name="ck_fiscal_invoices_breakdown_sum",
        ),
        sa.CheckConstraint("total_cents > 0", name="ck_fiscal_invoices_total_positive"),
        sa.ForeignKeyConstraint(["cai_range_id"], ["cai_ranges.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["work_orders.id"]),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cai_range_id", "correlative", name="uq_fiscal_invoices_range_correlative"
        ),
        sa.UniqueConstraint("workshop_id", "number", name="uq_fiscal_invoices_workshop_number"),
    )
    op.create_index("ix_fiscal_invoices_order_id", "fiscal_invoices", ["order_id"])
    op.create_index(
        "uq_fiscal_invoices_order_active",
        "fiscal_invoices",
        ["order_id"],
        unique=True,
        postgresql_where=sa.text("credited_at IS NULL"),
    )

    op.create_table(
        "fiscal_invoice_lines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workshop_id", sa.Uuid(), nullable=False),
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("source_line_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("line_total_cents", sa.BigInteger(), nullable=False),
        sa.CheckConstraint(
            "line_total_cents = quantity::bigint * unit_price_cents",
            name="ck_fiscal_invoice_lines_total",
        ),
        sa.ForeignKeyConstraint(["invoice_id"], ["fiscal_invoices.id"]),
        sa.ForeignKeyConstraint(["source_line_id"], ["work_order_lines.id"]),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "invoice_id", "position", name="uq_fiscal_invoice_lines_invoice_position"
        ),
    )
    op.create_index("ix_fiscal_invoice_lines_workshop_id", "fiscal_invoice_lines", ["workshop_id"])
    op.create_index(
        "ix_fiscal_invoice_lines_source_line_id", "fiscal_invoice_lines", ["source_line_id"]
    )

    # Immutability triggers (AD-10). Not expressible on the ORM models, so
    # they add no autogenerate drift: alembic check never compares
    # triggers.
    op.execute(
        f"CREATE OR REPLACE FUNCTION {_INVOICE_GUARD_FUNCTION}() RETURNS trigger "
        "LANGUAGE plpgsql AS $$ "
        "DECLARE "
        "    old_with_matched_credited_at fiscal_invoices; "
        "BEGIN "
        "    IF TG_OP = 'DELETE' THEN "
        "        RAISE EXCEPTION "
        "            'fiscal_invoices rows are immutable and cannot be deleted (id=%)', OLD.id; "
        "    END IF; "
        "    old_with_matched_credited_at := OLD; "
        "    old_with_matched_credited_at.credited_at := NEW.credited_at; "
        "    IF old_with_matched_credited_at IS DISTINCT FROM NEW THEN "
        "        RAISE EXCEPTION "
        "            'fiscal_invoices rows are immutable except for crediting (id=%)', OLD.id; "
        "    END IF; "
        "    IF NEW.credited_at IS DISTINCT FROM OLD.credited_at "
        "       AND OLD.credited_at IS NOT NULL THEN "
        "        RAISE EXCEPTION "
        "            'fiscal_invoices.credited_at can only be set once (id=%)', OLD.id; "
        "    END IF; "
        "    RETURN NEW; "
        "END; "
        "$$"
    )
    op.execute(
        f"CREATE TRIGGER {_INVOICE_GUARD_FUNCTION} "
        "BEFORE UPDATE OR DELETE ON fiscal_invoices "
        f"FOR EACH ROW EXECUTE FUNCTION {_INVOICE_GUARD_FUNCTION}()"
    )
    op.execute(
        f"CREATE OR REPLACE FUNCTION {_APPEND_ONLY_FUNCTION}() RETURNS trigger "
        "LANGUAGE plpgsql AS $$ "
        "BEGIN "
        "    RAISE EXCEPTION "
        "        '% rows are append-only and cannot be updated or deleted (id=%)', "
        "        TG_TABLE_NAME, OLD.id; "
        "END; "
        "$$"
    )
    op.execute(
        f"CREATE TRIGGER {_APPEND_ONLY_FUNCTION} "
        "BEFORE UPDATE OR DELETE ON fiscal_invoice_lines "
        f"FOR EACH ROW EXECUTE FUNCTION {_APPEND_ONLY_FUNCTION}()"
    )


def _guard_against_destroying_fiscal_documents() -> None:
    """AD-20: refuse to downgrade over real fiscal documents.

    Documents must be kept for custody (Art. 5, 41, 43); a bad release is
    reverted in code only. The one exception is the disposable public
    demo, which passes ``-x discard_fiscal_documents=demo`` after dumping
    the database first (see deploy/demo/README.md).
    """
    connection = op.get_bind()
    has_invoices = connection.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM fiscal_invoices)")
    ).scalar()
    if not has_invoices:
        return
    x_args = context.get_x_argument(as_dictionary=True)
    if x_args.get(_DISCARD_FLAG) != _DISCARD_FLAG_VALUE:
        raise RuntimeError(
            "Refusing to downgrade: fiscal_invoices holds documents that must be kept for "
            "custody (Art. 5, 41, 43). Re-run with "
            f"'-x {_DISCARD_FLAG}={_DISCARD_FLAG_VALUE}' only on the disposable demo database, "
            "after dumping it."
        )


def downgrade() -> None:
    """Downgrade schema."""
    _guard_against_destroying_fiscal_documents()

    op.execute(f"DROP TRIGGER IF EXISTS {_APPEND_ONLY_FUNCTION} ON fiscal_invoice_lines")
    op.execute(f"DROP FUNCTION IF EXISTS {_APPEND_ONLY_FUNCTION}()")
    op.execute(f"DROP TRIGGER IF EXISTS {_INVOICE_GUARD_FUNCTION} ON fiscal_invoices")
    op.execute(f"DROP FUNCTION IF EXISTS {_INVOICE_GUARD_FUNCTION}()")

    op.drop_index("ix_fiscal_invoice_lines_source_line_id", table_name="fiscal_invoice_lines")
    op.drop_index("ix_fiscal_invoice_lines_workshop_id", table_name="fiscal_invoice_lines")
    op.drop_table("fiscal_invoice_lines")

    op.drop_index(
        "uq_fiscal_invoices_order_active",
        table_name="fiscal_invoices",
        postgresql_where=sa.text("credited_at IS NULL"),
    )
    op.drop_index("ix_fiscal_invoices_order_id", table_name="fiscal_invoices")
    op.drop_table("fiscal_invoices")

    op.drop_index("ix_cai_ranges_workshop_id_document_type", table_name="cai_ranges")
    op.drop_table("cai_ranges")

    op.drop_table("fiscal_profiles")

    op.drop_constraint("ck_customers_rtn_digits", "customers", type_="check")
    op.drop_column("customers", "rtn")
    op.drop_column("customers", "billing_name")
