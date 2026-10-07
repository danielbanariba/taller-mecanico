"""add work orders and link stock movements to them

Revision ID: 8db9fb7d17ef
Revises: 1b224b5a2186
Create Date: 2026-10-07 09:41:18.964577

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8db9fb7d17ef"
down_revision: str | Sequence[str] | None = "1b224b5a2186"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Postgres' own default name for an ALTER-added foreign key
#: (`<table>_<column>_fkey`), named explicitly so `downgrade()` can drop it
#: without relying on autogenerate's unnamed-constraint placeholder.
_ORDER_ID_FK = "inventory_movements_order_id_fkey"
_ORDER_LINE_ID_FK = "inventory_movements_order_line_id_fkey"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "workshop_counters",
        sa.Column("workshop_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"]),
        sa.PrimaryKeyConstraint("workshop_id", "name"),
    )
    op.create_table(
        "work_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workshop_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("complaint", sa.Text(), nullable=True),
        sa.Column("odometer_km", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('quote', 'approved', 'in_progress', 'completed', 'delivered', 'cancelled')",
            name="ck_work_orders_status",
        ),
        sa.CheckConstraint(
            "odometer_km IS NULL OR odometer_km >= 0", name="ck_work_orders_odometer_nonneg"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workshop_id", "number", name="uq_work_orders_workshop_number"),
    )
    op.create_index(
        op.f("ix_work_orders_customer_id"), "work_orders", ["customer_id"], unique=False
    )
    op.create_index(op.f("ix_work_orders_vehicle_id"), "work_orders", ["vehicle_id"], unique=False)
    op.create_table(
        "work_order_lines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workshop_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=True),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("stock_posted_quantity", sa.Integer(), nullable=False),
        sa.Column("stock_revision", sa.Integer(), nullable=False),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "(kind = 'inventory_part') = (item_id IS NOT NULL)",
            name="ck_work_order_lines_item_matches_kind",
        ),
        sa.CheckConstraint(
            "kind = 'inventory_part' OR (stock_posted_quantity = 0 AND stock_revision = 0)",
            name="ck_work_order_lines_stock_only_parts",
        ),
        sa.CheckConstraint(
            "kind IN ('labor', 'inventory_part', 'external_part')",
            name="ck_work_order_lines_kind",
        ),
        sa.CheckConstraint(
            "quantity >= 1 AND quantity <= 10000", name="ck_work_order_lines_quantity"
        ),
        sa.CheckConstraint(
            "unit_price_cents >= 0 AND unit_price_cents <= 1000000000",
            name="ck_work_order_lines_unit_price",
        ),
        sa.ForeignKeyConstraint(["item_id"], ["inventory_items.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["work_orders.id"]),
        sa.ForeignKeyConstraint(["workshop_id"], ["workshops.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_work_order_lines_item_id"), "work_order_lines", ["item_id"], unique=False
    )
    op.create_index(
        op.f("ix_work_order_lines_order_id"), "work_order_lines", ["order_id"], unique=False
    )
    op.create_index(
        op.f("ix_work_order_lines_workshop_id"), "work_order_lines", ["workshop_id"], unique=False
    )

    # inventory_movements: nullable order-link columns, their FKs, the
    # link-pair check, then the two indexes (design.md's prescribed order).
    op.add_column("inventory_movements", sa.Column("order_id", sa.Uuid(), nullable=True))
    op.add_column("inventory_movements", sa.Column("order_line_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(_ORDER_ID_FK, "inventory_movements", "work_orders", ["order_id"], ["id"])
    op.create_foreign_key(
        _ORDER_LINE_ID_FK, "inventory_movements", "work_order_lines", ["order_line_id"], ["id"]
    )
    op.create_check_constraint(
        "ck_inventory_movements_order_link_pair",
        "inventory_movements",
        "(order_id IS NULL) = (order_line_id IS NULL)",
    )
    op.create_index(
        op.f("ix_inventory_movements_order_id"), "inventory_movements", ["order_id"], unique=False
    )
    op.create_index(
        op.f("ix_inventory_movements_order_line_id"),
        "inventory_movements",
        ["order_line_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # inventory_movements, in the reverse order: indexes, then the check and
    # both FKs, then the columns themselves. Linked movement rows remain, so
    # `Item.stock` still equals the ledger sum.
    op.drop_index(op.f("ix_inventory_movements_order_line_id"), table_name="inventory_movements")
    op.drop_index(op.f("ix_inventory_movements_order_id"), table_name="inventory_movements")
    op.drop_constraint(
        "ck_inventory_movements_order_link_pair", "inventory_movements", type_="check"
    )
    op.drop_constraint(_ORDER_LINE_ID_FK, "inventory_movements", type_="foreignkey")
    op.drop_constraint(_ORDER_ID_FK, "inventory_movements", type_="foreignkey")
    op.drop_column("inventory_movements", "order_line_id")
    op.drop_column("inventory_movements", "order_id")

    op.drop_index(op.f("ix_work_order_lines_workshop_id"), table_name="work_order_lines")
    op.drop_index(op.f("ix_work_order_lines_order_id"), table_name="work_order_lines")
    op.drop_index(op.f("ix_work_order_lines_item_id"), table_name="work_order_lines")
    op.drop_table("work_order_lines")
    op.drop_index(op.f("ix_work_orders_vehicle_id"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_customer_id"), table_name="work_orders")
    op.drop_table("work_orders")
    op.drop_table("workshop_counters")
