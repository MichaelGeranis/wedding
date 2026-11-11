"""Add sent column to invited_guests

Revision ID: ab12cd34ef56
Revises: 94c7be50cb0d
Create Date: 2025-12-07 12:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ab12cd34ef56"
down_revision: str | Sequence[str] | None = "94c7be50cb0d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("invited_guests", sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_index(op.f("ix_invited_guests_sent"), "invited_guests", ["sent"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_invited_guests_sent"), table_name="invited_guests")
    op.drop_column("invited_guests", "sent")
