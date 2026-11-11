
"""Add moderation history integrity constraints.

Revision ID: dcd0c799c600
Revises: b24e9fad9fd6
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision = "dcd0c799c600"
down_revision = "b24e9fad9fd6"
branch_labels = None
depends_on = None


# Adds database-level validation to moderation history.
def upgrade():

    connection = op.get_bind()
    dialect = connection.dialect.name

    # Reject migration if existing moderation records contain invalid statuses.
    invalid_history = connection.execute(
        sa.text("""
            SELECT id
            FROM moderation_history
            WHERE
                previous_status NOT IN ('pending', 'verified', 'rejected')
                OR new_status NOT IN ('pending', 'verified', 'rejected')
            LIMIT 1
        """)
    ).first()

    if invalid_history:
        raise RuntimeError(
            "Cannot add moderation history constraints: "
            f"invalid record found (ID: {invalid_history[0]})."
        )

    # Use triggers on SQLite to avoid rebuilding a referenced table.
    if dialect == "sqlite":

        op.execute("""
            CREATE TRIGGER trg_moderation_history_integrity_insert
            BEFORE INSERT ON moderation_history
            FOR EACH ROW
            WHEN
                NEW.previous_status NOT IN ('pending', 'verified', 'rejected')
                OR NEW.new_status NOT IN ('pending', 'verified', 'rejected')
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid moderation history status'
                );
            END;
        """)

        op.execute("""
            CREATE TRIGGER trg_moderation_history_integrity_update
            BEFORE UPDATE ON moderation_history
            FOR EACH ROW
            WHEN
                NEW.previous_status NOT IN ('pending', 'verified', 'rejected')
                OR NEW.new_status NOT IN ('pending', 'verified', 'rejected')
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid moderation history status'
                );
            END;
        """)

    # Use native CHECK constraints on PostgreSQL.
    else:

        op.create_check_constraint(
            "check_moderation_previous_status",
            "moderation_history",
            "previous_status IN ('pending', 'verified', 'rejected')"
        )

        op.create_check_constraint(
            "check_moderation_new_status",
            "moderation_history",
            "new_status IN ('pending', 'verified', 'rejected')"
        )


# Removes the moderation history validation rules.
def downgrade():

    connection = op.get_bind()

    if connection.dialect.name == "sqlite":

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_moderation_history_integrity_update"
        )

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_moderation_history_integrity_insert"
        )

    else:

        op.drop_constraint(
            "check_moderation_new_status",
            "moderation_history",
            type_="check"
        )

        op.drop_constraint(
            "check_moderation_previous_status",
            "moderation_history",
            type_="check"
        )
