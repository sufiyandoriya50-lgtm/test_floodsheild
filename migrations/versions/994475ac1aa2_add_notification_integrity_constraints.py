
"""add notification integrity constraints

Revision ID: 994475ac1aa2
Revises: dcd0c799c600
Create Date: 2026-11-11 17:57:59.384902

"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "994475ac1aa2"
down_revision = "dcd0c799c600"
branch_labels = None
depends_on = None


# Adds notification integrity constraints for SQLite and PostgreSQL.
def upgrade():

    # Check existing notification records before adding constraints.
    invalid_records = op.get_bind().execute(
        sa.text("""
            SELECT COUNT(*)
            FROM notifications
            WHERE
                length(trim(title)) = 0
                OR length(trim(message)) = 0
                OR length(trim(notification_type)) = 0
                OR (
                    deduplication_key IS NOT NULL
                    AND (
                        length(trim(deduplication_key)) = 0
                        OR length(deduplication_key) > 100
                    )
                )
                OR (
                    risk_level IS NOT NULL
                    AND risk_level NOT IN (
                        'low', 'moderate', 'high', 'severe'
                    )
                )
                OR (
                    latitude IS NOT NULL
                    AND (latitude < -90 OR latitude > 90)
                )
                OR (
                    longitude IS NOT NULL
                    AND (longitude < -180 OR longitude > 180)
                )
                OR delivery_status NOT IN (
                    'pending', 'no_devices', 'sent', 'partial', 'failed'
                )
        """)
    ).scalar()

    if invalid_records:
        raise RuntimeError(
            f"Cannot add notification constraints: "
            f"{invalid_records} invalid notification record(s) found."
        )

    # SQLite enforces the constraints through triggers.
    if op.get_bind().dialect.name == "sqlite":

        op.execute("""
            CREATE TRIGGER trg_notifications_integrity_insert
            BEFORE INSERT ON notifications
            FOR EACH ROW
            WHEN
                length(trim(NEW.title)) = 0
                OR length(trim(NEW.message)) = 0
                OR length(trim(NEW.notification_type)) = 0
                OR (
                    NEW.deduplication_key IS NOT NULL
                    AND (
                        length(trim(NEW.deduplication_key)) = 0
                        OR length(NEW.deduplication_key) > 100
                    )
                )
                OR (
                    NEW.risk_level IS NOT NULL
                    AND NEW.risk_level NOT IN (
                        'low', 'moderate', 'high', 'severe'
                    )
                )
                OR (
                    NEW.latitude IS NOT NULL
                    AND (NEW.latitude < -90 OR NEW.latitude > 90)
                )
                OR (
                    NEW.longitude IS NOT NULL
                    AND (NEW.longitude < -180 OR NEW.longitude > 180)
                )
                OR NEW.delivery_status NOT IN (
                    'pending', 'no_devices', 'sent', 'partial', 'failed'
                )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid notification integrity data'
                );
            END;
        """)

        op.execute("""
            CREATE TRIGGER trg_notifications_integrity_update
            BEFORE UPDATE ON notifications
            FOR EACH ROW
            WHEN
                length(trim(NEW.title)) = 0
                OR length(trim(NEW.message)) = 0
                OR length(trim(NEW.notification_type)) = 0
                OR (
                    NEW.deduplication_key IS NOT NULL
                    AND (
                        length(trim(NEW.deduplication_key)) = 0
                        OR length(NEW.deduplication_key) > 100
                    )
                )
                OR (
                    NEW.risk_level IS NOT NULL
                    AND NEW.risk_level NOT IN (
                        'low', 'moderate', 'high', 'severe'
                    )
                )
                OR (
                    NEW.latitude IS NOT NULL
                    AND (NEW.latitude < -90 OR NEW.latitude > 90)
                )
                OR (
                    NEW.longitude IS NOT NULL
                    AND (NEW.longitude < -180 OR NEW.longitude > 180)
                )
                OR NEW.delivery_status NOT IN (
                    'pending', 'no_devices', 'sent', 'partial', 'failed'
                )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid notification integrity data'
                );
            END;
        """)

    # PostgreSQL uses native CHECK constraints.
    elif op.get_bind().dialect.name == "postgresql":

        constraints = [
            (
                "check_notification_title",
                "length(trim(title)) > 0"
            ),
            (
                "check_notification_message",
                "length(trim(message)) > 0"
            ),
            (
                "check_notification_type",
                "length(trim(notification_type)) > 0"
            ),
            (
                "check_notification_deduplication_key",
                "deduplication_key IS NULL OR "
                "(length(trim(deduplication_key)) > 0 "
                "AND length(deduplication_key) <= 100)"
            ),
            (
                "check_notification_risk_level",
                "risk_level IS NULL OR "
                "risk_level IN ('low', 'moderate', 'high', 'severe')"
            ),
            (
                "check_notification_latitude",
                "latitude IS NULL OR "
                "(latitude >= -90 AND latitude <= 90)"
            ),
            (
                "check_notification_longitude",
                "longitude IS NULL OR "
                "(longitude >= -180 AND longitude <= 180)"
            ),
            (
                "check_notification_delivery_status",
                "delivery_status IN "
                "('pending', 'no_devices', 'sent', 'partial', 'failed')"
            ),
        ]

        for constraint_name, condition in constraints:
            op.create_check_constraint(
                constraint_name,
                "notifications",
                condition
            )


# Removes notification integrity constraints.
def downgrade():

    if op.get_bind().dialect.name == "sqlite":

        op.execute("""
            DROP TRIGGER IF EXISTS trg_notifications_integrity_insert
        """)

        op.execute("""
            DROP TRIGGER IF EXISTS trg_notifications_integrity_update
        """)

    elif op.get_bind().dialect.name == "postgresql":

        constraints = [
            "check_notification_title",
            "check_notification_message",
            "check_notification_type",
            "check_notification_deduplication_key",
            "check_notification_risk_level",
            "check_notification_latitude",
            "check_notification_longitude",
            "check_notification_delivery_status",
        ]

        for constraint_name in constraints:
            op.drop_constraint(
                constraint_name,
                "notifications",
                type_="check"
            )
