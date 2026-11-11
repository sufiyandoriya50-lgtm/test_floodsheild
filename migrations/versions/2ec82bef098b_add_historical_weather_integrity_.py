
"""Add historical weather integrity constraints."""

from alembic import op


# Revision identifiers, used by Alembic.
revision = "2ec82bef098b"
down_revision = "8e83f408c6bc"
branch_labels = None
depends_on = None


# Checks existing historical weather records before adding constraints.
def check_existing_historical_weather_records():
    """Reject migration if existing historical weather records are invalid."""

    connection = op.get_bind()

    invalid_record = connection.exec_driver_sql(
        """
        SELECT id
        FROM historical_weather_records
        WHERE
            latitude IS NULL
            OR latitude < -90
            OR latitude > 90
            OR longitude IS NULL
            OR longitude < -180
            OR longitude > 180
            OR rainfall_mm IS NULL
            OR rainfall_mm < 0
            OR (
                wind_speed_kmh IS NOT NULL
                AND wind_speed_kmh < 0
            )
            OR (
                precipitation_interval_seconds IS NOT NULL
                AND precipitation_interval_seconds <= 0
            )
            OR source IS NULL
            OR length(trim(source)) = 0
            OR length(source) > 100
        LIMIT 1
        """
    ).first()

    if invalid_record:
        raise RuntimeError(
            "Cannot apply historical weather constraints. "
            f"Invalid historical weather record ID: {invalid_record[0]}"
        )


# Adds integrity constraints for historical weather records.
def upgrade():
    """Add database-level historical weather integrity rules."""

    check_existing_historical_weather_records()

    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":

        op.execute(
            """
            CREATE TRIGGER trg_historical_weather_integrity_insert
            BEFORE INSERT ON historical_weather_records
            FOR EACH ROW
            WHEN
                NEW.latitude IS NULL
                OR NEW.latitude < -90
                OR NEW.latitude > 90
                OR NEW.longitude IS NULL
                OR NEW.longitude < -180
                OR NEW.longitude > 180
                OR NEW.rainfall_mm IS NULL
                OR NEW.rainfall_mm < 0
                OR (
                    NEW.wind_speed_kmh IS NOT NULL
                    AND NEW.wind_speed_kmh < 0
                )
                OR (
                    NEW.precipitation_interval_seconds IS NOT NULL
                    AND NEW.precipitation_interval_seconds <= 0
                )
                OR NEW.source IS NULL
                OR length(trim(NEW.source)) = 0
                OR length(NEW.source) > 100
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid historical weather record data'
                );
            END;
            """
        )

        op.execute(
            """
            CREATE TRIGGER trg_historical_weather_integrity_update
            BEFORE UPDATE ON historical_weather_records
            FOR EACH ROW
            WHEN
                NEW.latitude IS NULL
                OR NEW.latitude < -90
                OR NEW.latitude > 90
                OR NEW.longitude IS NULL
                OR NEW.longitude < -180
                OR NEW.longitude > 180
                OR NEW.rainfall_mm IS NULL
                OR NEW.rainfall_mm < 0
                OR (
                    NEW.wind_speed_kmh IS NOT NULL
                    AND NEW.wind_speed_kmh < 0
                )
                OR (
                    NEW.precipitation_interval_seconds IS NOT NULL
                    AND NEW.precipitation_interval_seconds <= 0
                )
                OR NEW.source IS NULL
                OR length(trim(NEW.source)) = 0
                OR length(NEW.source) > 100
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid historical weather record data'
                );
            END;
            """
        )

    elif dialect == "postgresql":

        op.create_check_constraint(
            "check_historical_weather_latitude",
            "historical_weather_records",
            "latitude >= -90 AND latitude <= 90"
        )

        op.create_check_constraint(
            "check_historical_weather_longitude",
            "historical_weather_records",
            "longitude >= -180 AND longitude <= 180"
        )

        op.create_check_constraint(
            "check_historical_weather_rainfall",
            "historical_weather_records",
            "rainfall_mm >= 0"
        )

        op.create_check_constraint(
            "check_historical_weather_wind_speed",
            "historical_weather_records",
            "wind_speed_kmh IS NULL OR wind_speed_kmh >= 0"
        )

        op.create_check_constraint(
            "check_historical_weather_precipitation_interval",
            "historical_weather_records",
            "precipitation_interval_seconds IS NULL "
            "OR precipitation_interval_seconds > 0"
        )

        op.create_check_constraint(
            "check_historical_weather_source",
            "historical_weather_records",
            "length(trim(source)) > 0 AND length(source) <= 100"
        )

    else:
        raise RuntimeError(
            f"Unsupported database dialect: {dialect}"
        )


# Removes historical weather integrity constraints.
def downgrade():
    """Remove historical weather database integrity rules."""

    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_historical_weather_integrity_insert"
        )

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_historical_weather_integrity_update"
        )

    elif dialect == "postgresql":

        op.drop_constraint(
            "check_historical_weather_source",
            "historical_weather_records",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_weather_precipitation_interval",
            "historical_weather_records",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_weather_wind_speed",
            "historical_weather_records",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_weather_rainfall",
            "historical_weather_records",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_weather_longitude",
            "historical_weather_records",
            type_="check"
        )

        op.drop_constraint(
            "check_historical_weather_latitude",
            "historical_weather_records",
            type_="check"
        )

    else:
        raise RuntimeError(
            f"Unsupported database dialect: {dialect}"
        )
