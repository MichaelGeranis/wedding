"""Add Greek translation fields to invitations

Revision ID: a1b2c3d4e5f6
Revises: f4cab136eec2
Create Date: 2025-12-17 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f4cab136eec2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add Greek translation fields for names, church and venue."""
    # Church Greek fields
    op.add_column("invitations", sa.Column("church_name_gr", sa.String(200), nullable=True))
    op.add_column("invitations", sa.Column("church_address_gr", sa.Text(), nullable=True))
    op.add_column("invitations", sa.Column("church_city_gr", sa.String(100), nullable=True))
    # Venue Greek fields
    op.add_column("invitations", sa.Column("venue_name_gr", sa.String(200), nullable=True))
    op.add_column("invitations", sa.Column("venue_address_gr", sa.Text(), nullable=True))
    op.add_column("invitations", sa.Column("venue_city_gr", sa.String(100), nullable=True))


def downgrade() -> None:
    """Remove Greek translation fields."""
    op.drop_column("invitations", "venue_city_gr")
    op.drop_column("invitations", "venue_address_gr")
    op.drop_column("invitations", "venue_name_gr")
    op.drop_column("invitations", "church_city_gr")
    op.drop_column("invitations", "church_address_gr")
    op.drop_column("invitations", "church_name_gr")
