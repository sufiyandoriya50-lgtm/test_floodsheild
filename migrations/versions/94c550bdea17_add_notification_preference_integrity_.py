
"""Add notification preference integrity constraints."""

from alembic import op
import sqlalchemy as sa


revision = "94c550bdea17"
down_revision = "d4a5cd3bcf6c"
branch_labels = None
depends_on = None


# Check existing notification preferences before applying constraints.
def check_existing_preferences():
    """Reject migration if existing preferences contain invalid values."""

    connection = op.get_bind()
    dialect = connection.dialect.name

    if dialect == "sqlite":
        invalid_record = connection.execute(
            sa.text("""
                SELECT id
                FROM notification_preferences
                WHERE push_enabled NOT IN (0, 1)
                   OR high_risk_enabled NOT IN (0, 1)
                   OR severe_risk_enabled NOT IN (0, 1)
                   OR push_enabled IS NULL
                   OR high_risk_enabled IS NULL
                   OR severe_risk_enabled IS NULL
                LIMIT 1
            """)
        ).first()

        if invalid_record:
            raise RuntimeError(
                "Invalid notification preference record found: "
                f"{invalid_record[0]}"
            )

    elif dialect == "postgresql":
        invalid_record = connection.execute(
            sa.text("""
                SELECT id
                FROM notification_preferences
                WHERE push_enabled IS NULL
                   OR high_risk_enabled IS NULL
                   OR severe_risk_enabled IS NULL
                LIMIT 1
            """)
        ).first()

        if invalid_record:
            raise RuntimeError(
                "Invalid notification preference record found: "
                f"{invalid_record[0]}"
            )


# Apply notification preference integrity constraints.
def upgrade():
    """Enforce valid Boolean notification preference values."""

    check_existing_preferences()

    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":

        op.execute("""
            CREATE TRIGGER
            trg_notification_preferences_integrity_insert
            BEFORE INSERT ON notification_preferences
            FOR EACH ROW
            WHEN NEW.push_enabled NOT IN (0, 1)
              OR NEW.high_risk_enabled NOT IN (0, 1)
              OR NEW.severe_risk_enabled NOT IN (0, 1)
              OR NEW.push_enabled IS NULL
              OR NEW.high_risk_enabled IS NULL
              OR NEW.severe_risk_enabled IS NULL
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid notification preference data'
                );
            END;
        """)

        op.execute("""
            CREATE TRIGGER
            trg_notification_preferences_integrity_update
            BEFORE UPDATE ON notification_preferences
            FOR EACH ROW
            WHEN NEW.push_enabled NOT IN (0, 1)
              OR NEW.high_risk_enabled NOT IN (0, 1)
              OR NEW.severe_risk_enabled NOT IN (0, 1)
              OR NEW.push_enabled IS NULL
              OR NEW.high_risk_enabled IS NULL
              OR NEW.severe_risk_enabled IS NULL
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid notification preference data'
                );
            END;
        """)

    elif dialect == "postgresql":

        op.create_check_constraint(
            "check_notification_preference_push",
            "notification_preferences",
            "push_enabled IN (TRUE, FALSE)"
        )

        op.create_check_constraint(
            "check_notification_preference_high_risk",
            "notification_preferences",
            "high_risk_enabled IN (TRUE, FALSE)"
        )

        op.create_check_constraint(
            "check_notification_preference_severe_risk",
            "notification_preferences",
            "severe_risk_enabled IN (TRUE, FALSE)"
        )

    else:
        raise RuntimeError(
            f"Unsupported database dialect: {dialect}"
        )


# Remove notification preference integrity constraints.
def downgrade():
    """Remove notification preference integrity constraints."""

    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_notification_preferences_integrity_insert"
        )

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_notification_preferences_integrity_update"
        )

    elif dialect == "postgresql":

        op.drop_constraint(
            "check_notification_preference_severe_risk",
            "notification_preferences",
            type_="check"
        )

        op.drop_constraint(
            "check_notification_preference_high_risk",
            "notification_preferences",
            type_="check"
        )

        op.drop_constraint(
            "check_notification_preference_push",
            "notification_preferences",
            type_="check"
        )
