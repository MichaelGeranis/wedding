"""add token field to invited_guests

Revision ID: 173e6b4f4177
Revises: 5f2d1183a98e
Create Date: 2025-12-12 13:04:16.086746

"""

import secrets
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "173e6b4f4177"
down_revision: Union[str, Sequence[str], None] = "5f2d1183a98e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add column as nullable first
    op.add_column("invited_guests", sa.Column("token", sa.String(length=64), nullable=True))

    # Generate tokens for existing rows
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id FROM invited_guests"))
    rows = result.fetchall()

    for row in rows:
        token = secrets.token_urlsafe(32)
        connection.execute(sa.text("UPDATE invited_guests SET token = :token WHERE id = :id"), {"token": token, "id": row[0]})

    # Now make the column non-nullable and add unique constraint
    op.alter_column("invited_guests", "token", nullable=False)
    op.create_index(op.f("ix_invited_guests_token"), "invited_guests", ["token"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_invited_guests_token"), table_name="invited_guests")
    op.drop_column("invited_guests", "token")
