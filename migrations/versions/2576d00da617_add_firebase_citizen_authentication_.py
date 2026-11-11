
"""Add Firebase citizen authentication fields.

Revision ID: 2576d00da617
Revises: 76b5028b7e91
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision = "2576d00da617"
down_revision = "76b5028b7e91"
branch_labels = None
depends_on = None


# Adds Firebase authentication fields to citizen accounts.
def upgrade():

    with op.batch_alter_table("users", schema=None) as batch_op:

        batch_op.add_column(
            sa.Column("firebase_uid", sa.String(length=128), nullable=True)
        )

        batch_op.add_column(
            sa.Column("phone_number", sa.String(length=20), nullable=True)
        )

        batch_op.alter_column(
            "email",
            existing_type=sa.VARCHAR(length=120),
            nullable=True
        )

        batch_op.alter_column(
            "password_hash",
            existing_type=sa.VARCHAR(length=256),
            nullable=True
        )

        batch_op.create_unique_constraint(
            "uq_users_phone_number",
            ["phone_number"]
        )

        batch_op.create_unique_constraint(
            "uq_users_firebase_uid",
            ["firebase_uid"]
        )


# Reverses the Firebase authentication schema changes.
def downgrade():

    with op.batch_alter_table("users", schema=None) as batch_op:

        batch_op.drop_constraint(
            "uq_users_firebase_uid",
            type_="unique"
        )

        batch_op.drop_constraint(
            "uq_users_phone_number",
            type_="unique"
        )

        batch_op.alter_column(
            "password_hash",
            existing_type=sa.VARCHAR(length=256),
            nullable=False
        )

        batch_op.alter_column(
            "email",
            existing_type=sa.VARCHAR(length=120),
            nullable=False
        )

        batch_op.drop_column("phone_number")
        batch_op.drop_column("firebase_uid")
