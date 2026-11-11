"""Change user password to password_hash with bcrypt hashing

Revision ID: 558645b6f7ce
Revises: 6982fe22af48
Create Date: 2025-12-11 12:51:29.679626

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "558645b6f7ce"
down_revision: str | Sequence[str] | None = "6982fe22af48"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - rename password to password_hash and increase length."""
    # Rename column from 'password' to 'password_hash'
    op.alter_column("users", "password", new_column_name="password_hash")

    # Alter column type to allow longer bcrypt hashes (60 chars)
    op.alter_column("users", "password_hash", type_=sa.String(255), existing_type=sa.String(100))


def downgrade() -> None:
    """Downgrade schema - revert password_hash to password."""
    # Revert column type
    op.alter_column("users", "password_hash", type_=sa.String(100), existing_type=sa.String(255))

    # Rename column back
    op.alter_column("users", "password_hash", new_column_name="password")
