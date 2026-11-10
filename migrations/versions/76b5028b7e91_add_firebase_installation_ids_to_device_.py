
"""Add Firebase installation IDs to device tokens

Revision ID: 76b5028b7e91
Revises: a3f810afb35a
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision = "76b5028b7e91"
down_revision = "a3f810afb35a"
branch_labels = None
depends_on = None


# Adds the FID column while preserving existing legacy device tokens.
def upgrade():
    with op.batch_alter_table("device_tokens", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("fid", sa.String(length=512), nullable=True)
        )
        batch_op.alter_column(
            "token",
            existing_type=sa.VARCHAR(length=512),
            nullable=True
        )
        batch_op.create_unique_constraint(
            "uq_device_tokens_fid",
            ["fid"]
        )


# Reverses the FID migration while preserving the legacy token column.
def downgrade():
    with op.batch_alter_table("device_tokens", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_device_tokens_fid",
            type_="unique"
        )
        batch_op.alter_column(
            "token",
            existing_type=sa.VARCHAR(length=512),
            nullable=False
        )
        batch_op.drop_column("fid")
