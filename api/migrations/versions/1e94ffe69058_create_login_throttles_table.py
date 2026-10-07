"""create login_throttles table

Revision ID: 1e94ffe69058
Revises: 3571335f9414
Create Date: 2026-10-06 19:16:14.258436

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1e94ffe69058"
down_revision: str | Sequence[str] | None = "3571335f9414"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "login_throttles",
        sa.Column("phone", sa.String(length=8), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("phone"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("login_throttles")
