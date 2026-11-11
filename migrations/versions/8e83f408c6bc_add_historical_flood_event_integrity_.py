
"""Add historical flood event integrity constraints."""

from alembic import op


# Revision identifiers, used by Alembic.
revision = "8e83f408c6bc"
down_revision = "94c550bdea17"
branch_labels = None
depends_on = None


# Checks existing historical flood records before adding constraints.
def check_existing_historical_flood_events():
    """Reject migration if existing historical flood records are invalid."""

    connection = op.get_bind()

    invalid_record = connection.exec_driver_sql(
        """
        SELECT id
        FROM historical_flood_events
        WHERE
            latitude IS NULL
            OR latitude < -90
            OR latitude > 90
            OR longitude IS NULL
            OR longitude < -180
            OR longitude > 180
            OR water_depth_cm < 0
            OR (
                severity IS NOT NULL
                AND severity NOT IN ('low', 'moderate', 'high', 'severe')
            )
            OR source IS NULL
            OR length(trim(source)) = 0
            OR length(source) > 100
            OR (
                event_name IS NOT NULL
                AND (
                    length(trim(event_name)) = 0
                    OR length(event_name) > 150
                )
            )
            OR (
                source_reference IS NOT NULL
                AND (
                    length(trim(source_reference)) = 0
                    OR length(source_reference) > 500
                )
            )
        LIMIT 1
        """
    ).first()

    if invalid_record:
        raise RuntimeError(
            "Cannot apply historical flood constraints. "
            f"Invalid historical flood event ID: {invalid_record[0]}"
        )


# Adds integrity constraints for historical flood events.
def upgrade():
    """Add database-level historical flood event integrity rules."""

    check_existing_historical_flood_events()

    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":

        op.execute(
            """
            CREATE TRIGGER trg_historical_flood_integrity_insert
            BEFORE INSERT ON historical_flood_events
            FOR EACH ROW
            WHEN
                NEW.latitude IS NULL
                OR NEW.latitude < -90
                OR NEW.latitude > 90
                OR NEW.longitude IS NULL
                OR NEW.longitude < -180
                OR NEW.longitude > 180
                OR (
                    NEW.water_depth_cm IS NOT NULL
                    AND NEW.water_depth_cm < 0
                )
                OR (
                    NEW.severity IS NOT NULL
                    AND NEW.severity NOT IN (
                        'low', 'moderate', 'high', 'severe'
                    )
                )
                OR NEW.source IS NULL
                OR length(trim(NEW.source)) = 0
                OR length(NEW.source) > 100
                OR (
                    NEW.event_name IS NOT NULL
                    AND (
                        length(trim(NEW.event_name)) = 0
                        OR length(NEW.event_name) > 150
                    )
                )
                OR (
                    NEW.source_reference IS NOT NULL
                    AND (
                        length(trim(NEW.source_reference)) = 0
                        OR length(NEW.source_reference) > 500
                    )
                )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid historical flood event data'
                );
            END;
            """
        )

        op.execute(
            """
            CREATE TRIGGER trg_historical_flood_integrity_update
            BEFORE UPDATE ON historical_flood_events
            FOR EACH ROW
            WHEN
                NEW.latitude IS NULL
                OR NEW.latitude < -90
                OR NEW.latitude > 90
                OR NEW.longitude IS NULL
                OR NEW.longitude < -180
                OR NEW.longitude > 180
                OR (
                    NEW.water_depth_cm IS NOT NULL
                    AND NEW.water_depth_cm < 0
                )
                OR (
                    NEW.severity IS NOT NULL
                    AND NEW.severity NOT IN (
                        'low', 'moderate', 'high', 'severe'
                    )
                )
                OR NEW.source IS NULL
                OR length(trim(NEW.source)) = 0
                OR length(NEW.source) > 100
                OR (
                    NEW.event_name IS NOT NULL
                    AND (
                        length(trim(NEW.event_name)) = 0
                        OR length(NEW.event_name) > 150
                    )
                )
                OR (
                    NEW.source_reference IS NOT NULL
                    AND (
                        length(trim(NEW.source_reference)) = 0
                        OR length(NEW.source_reference) > 500
                    )
                )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid historical flood event data'
                );
            END;
            """
        )

    elif dialect == "postgresql":

        op.create_check_constraint(
            "check_historical_flood_latitude",
            "historical_flood_events",
            "latitude >= -90 AND latitude <= 90"
        )

        op.create_check_constraint(
            "check_historical_flood_longitude",
            "historical_flood_events",
            "longitude >= -180 AND longitude <= 180"
        )

        op.create_check_constraint(
            "check_historical_flood_water_depth",
            "historical_flood_events",
            "water_depth_cm IS NULL OR water_depth_cm >= 0"
        )

        op.create_check_constraint(
            "check_historical_flood_severity",
            "historical_flood_events",
            "severity IS NULL OR severity IN "
            "('low', 'moderate', 'high', 'severe')"
        )

        op.create_check_constraint(
            "check_historical_flood_source",
            "historical_flood_events",
            "length(trim(source)) > 0 AND length(source) <= 100"
        )

        op.create_check_constraint(
            "check_historical_flood_event_name",
            "historical_flood_events",
            "event_name IS NULL OR "
            "(length(trim(event_name)) > 0 AND length(event_name) <= 150)"
        )

        op.create_check_constraint(
            "check_historical_flood_source_reference",
            "historical_flood_events",
            "source_reference IS NULL OR "
            "(length(trim(source_reference)) > 0 "
            "AND length(source_reference) <= 500)"
        )

    else:
        raise RuntimeError(
            f"Unsupported database dialect: {dialect}"
        )


# Removes historical flood-event integrity constraints.
def downgrade():
    """Remove historical flood event database integrity rules."""

    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_historical_flood_integrity_insert"
        )

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_historical_flood_integrity_update"
        )

    elif dialect == "postgresql":

        op.drop_constraint(
            "check_historical_flood_source_reference",
            "historical_flood_events",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_flood_event_name",
            "historical_flood_events",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_flood_source",
            "historical_flood_events",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_flood_severity",
            "historical_flood_events",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_flood_water_depth",
            "historical_flood_events",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_flood_longitude",
            "historical_flood_events",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_flood_latitude",
            "historical_flood_events",
            type_="check"
        )

    else:
        raise RuntimeError(
            f"Unsupported database dialect: {dialect}"
        )
