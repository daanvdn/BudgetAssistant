"""Remove username column from user table

Revision ID: remove_username
Revises: fa9439f92ead
Create Date: 2026-01-31

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "remove_username"
down_revision: Union[str, None] = "fa9439f92ead"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the username index first
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_username"))

    # Drop the username column
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("username")

    # Create index on email if not already exists
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_email"), ["email"], unique=True)


def downgrade() -> None:
    # Drop email index
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_user_email"))

    # Re-add the username column
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("username", sa.String(length=150), nullable=False, server_default="")
        )

    # Re-create the username index
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_user_username"), ["username"], unique=True)
