
"""add user integrity constraints

Revision ID: cf8d4bdc7fd3
Revises: 186d7c1439fc
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "cf8d4bdc7fd3"
down_revision = "186d7c1439fc"
branch_labels = None
depends_on = None


# Adds database-level integrity rules to user accounts.
def upgrade():
    """Add user integrity constraints."""

    connection = op.get_bind()

    # Check existing records before applying constraints.
    invalid_records = connection.execute(
        sa.text("""
            SELECT id
            FROM users
            WHERE
                name IS NULL
                OR length(trim(name)) = 0
                OR length(name) > 100

                OR role IS NULL
                OR role NOT IN ('citizen', 'admin')

                OR (
                    email IS NOT NULL
                    AND (
                        length(trim(email)) = 0
                        OR length(email) > 120
                    )
                )

                OR (
                    password_hash IS NOT NULL
                    AND length(trim(password_hash)) = 0
                )

                OR (
                    firebase_uid IS NOT NULL
                    AND (
                        length(trim(firebase_uid)) = 0
                        OR length(firebase_uid) > 128
                    )
                )

                OR (
                    phone_number IS NOT NULL
                    AND (
                        length(trim(phone_number)) = 0
                        OR length(phone_number) > 20
                    )
                )
            LIMIT 10
        """)
    ).fetchall()

    if invalid_records:
        raise RuntimeError(
            "Cannot apply user integrity constraints. "
            f"Invalid user IDs: {invalid_records}"
        )

    # SQLite uses triggers to enforce the integrity rules.
    if connection.dialect.name == "sqlite":

        op.execute("""
            CREATE TRIGGER trg_user_integrity_insert
            BEFORE INSERT ON users
            FOR EACH ROW
            WHEN
                NEW.name IS NULL
                OR length(trim(NEW.name)) = 0
                OR length(NEW.name) > 100

                OR NEW.role IS NULL
                OR NEW.role NOT IN ('citizen', 'admin')

                OR (
                    NEW.email IS NOT NULL
                    AND (
                        length(trim(NEW.email)) = 0
                        OR length(NEW.email) > 120
                    )
                )

                OR (
                    NEW.password_hash IS NOT NULL
                    AND length(trim(NEW.password_hash)) = 0
                )

                OR (
                    NEW.firebase_uid IS NOT NULL
                    AND (
                        length(trim(NEW.firebase_uid)) = 0
                        OR length(NEW.firebase_uid) > 128
                    )
                )

                OR (
                    NEW.phone_number IS NOT NULL
                    AND (
                        length(trim(NEW.phone_number)) = 0
                        OR length(NEW.phone_number) > 20
                    )
                )
            BEGIN
                SELECT RAISE(ABORT, 'Invalid user account data');
            END;
        """)

        op.execute("""
            CREATE TRIGGER trg_user_integrity_update
            BEFORE UPDATE ON users
            FOR EACH ROW
            WHEN
                NEW.name IS NULL
                OR length(trim(NEW.name)) = 0
                OR length(NEW.name) > 100

                OR NEW.role IS NULL
                OR NEW.role NOT IN ('citizen', 'admin')

                OR (
                    NEW.email IS NOT NULL
                    AND (
                        length(trim(NEW.email)) = 0
                        OR length(NEW.email) > 120
                    )
                )

                OR (
                    NEW.password_hash IS NOT NULL
                    AND length(trim(NEW.password_hash)) = 0
                )

                OR (
                    NEW.firebase_uid IS NOT NULL
                    AND (
                        length(trim(NEW.firebase_uid)) = 0
                        OR length(NEW.firebase_uid) > 128
                    )
                )

                OR (
                    NEW.phone_number IS NOT NULL
                    AND (
                        length(trim(NEW.phone_number)) = 0
                        OR length(NEW.phone_number) > 20
                    )
                )
            BEGIN
                SELECT RAISE(ABORT, 'Invalid user account data');
            END;
        """)

    # PostgreSQL uses native CHECK constraints.
    elif connection.dialect.name == "postgresql":

        with op.batch_alter_table("users") as batch_op:

            batch_op.create_check_constraint(
                "check_user_name",
                "length(trim(name)) > 0 AND length(name) <= 100"
            )

            batch_op.create_check_constraint(
                "check_user_role",
                "role IN ('citizen', 'admin')"
            )

            batch_op.create_check_constraint(
                "check_user_email",
                "email IS NULL OR "
                "(length(trim(email)) > 0 AND length(email) <= 120)"
            )

            batch_op.create_check_constraint(
                "check_user_password_hash",
                "password_hash IS NULL OR "
                "length(trim(password_hash)) > 0"
            )

            batch_op.create_check_constraint(
                "check_user_firebase_uid",
                "firebase_uid IS NULL OR "
                "(length(trim(firebase_uid)) > 0 "
                "AND length(firebase_uid) <= 128)"
            )

            batch_op.create_check_constraint(
                "check_user_phone_number",
                "phone_number IS NULL OR "
                "(length(trim(phone_number)) > 0 "
                "AND length(phone_number) <= 20)"
            )


# Removes user integrity constraints.
def downgrade():
    """Remove user integrity constraints."""

    connection = op.get_bind()

    if connection.dialect.name == "sqlite":

        op.execute(
            "DROP TRIGGER IF EXISTS trg_user_integrity_insert"
        )

        op.execute(
            "DROP TRIGGER IF EXISTS trg_user_integrity_update"
        )

    elif connection.dialect.name == "postgresql":

        with op.batch_alter_table("users") as batch_op:

            batch_op.drop_constraint(
                "check_user_name",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_user_role",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_user_email",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_user_password_hash",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_user_firebase_uid",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_user_phone_number",
                type_="check"
            )
