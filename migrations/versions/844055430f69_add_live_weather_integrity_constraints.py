
"""add live weather integrity constraints

Revision ID: 844055430f69
Revises: 2ec82bef098b
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "844055430f69"
down_revision = "2ec82bef098b"
branch_labels = None
depends_on = None


# Adds database-level validation for live weather records.
def upgrade():
    """Add integrity constraints to live weather records."""

    connection = op.get_bind()

    # Check existing records before adding integrity constraints.
    invalid_records = connection.execute(
        sa.text("""
            SELECT id
            FROM weather_records
            WHERE
                latitude IS NULL
                OR latitude < -90
                OR latitude > 90
                OR longitude IS NULL
                OR longitude < -180
                OR longitude > 180
                OR (
                    rainfall_mm IS NOT NULL
                    AND rainfall_mm < 0
                )
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
                OR length(source) > 50
            LIMIT 10
        """)
    ).fetchall()

    if invalid_records:
        raise RuntimeError(
            "Cannot apply live weather integrity constraints. "
            f"Invalid weather record IDs: {invalid_records}"
        )

    # Add SQLite triggers for INSERT and UPDATE operations.
    if connection.dialect.name == "sqlite":

        op.execute("""
            CREATE TRIGGER trg_weather_integrity_insert
            BEFORE INSERT ON weather_records
            FOR EACH ROW
            WHEN
                NEW.latitude IS NULL
                OR NEW.latitude < -90
                OR NEW.latitude > 90
                OR NEW.longitude IS NULL
                OR NEW.longitude < -180
                OR NEW.longitude > 180
                OR (
                    NEW.rainfall_mm IS NOT NULL
                    AND NEW.rainfall_mm < 0
                )
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
                OR length(NEW.source) > 50
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid live weather record'
                );
            END;
        """)

        op.execute("""
            CREATE TRIGGER trg_weather_integrity_update
            BEFORE UPDATE ON weather_records
            FOR EACH ROW
            WHEN
                NEW.latitude IS NULL
                OR NEW.latitude < -90
                OR NEW.latitude > 90
                OR NEW.longitude IS NULL
                OR NEW.longitude < -180
                OR NEW.longitude > 180
                OR (
                    NEW.rainfall_mm IS NOT NULL
                    AND NEW.rainfall_mm < 0
                )
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
                OR length(NEW.source) > 50
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid live weather record'
                );
            END;
        """)

    # Add native CHECK constraints for PostgreSQL.
    elif connection.dialect.name == "postgresql":

        with op.batch_alter_table(
            "weather_records"
        ) as batch_op:

            batch_op.create_check_constraint(
                "check_weather_latitude",
                "latitude >= -90 AND latitude <= 90"
            )

            batch_op.create_check_constraint(
                "check_weather_longitude",
                "longitude >= -180 AND longitude <= 180"
            )

            batch_op.create_check_constraint(
                "check_weather_rainfall",
                "rainfall_mm IS NULL OR rainfall_mm >= 0"
            )

            batch_op.create_check_constraint(
                "check_weather_wind_speed",
                "wind_speed_kmh IS NULL OR wind_speed_kmh >= 0"
            )

            batch_op.create_check_constraint(
                "check_weather_precipitation_interval",
                "precipitation_interval_seconds IS NULL "
                "OR precipitation_interval_seconds > 0"
            )

            batch_op.create_check_constraint(
                "check_weather_source",
                "length(trim(source)) > 0 AND length(source) <= 50"
            )


# Removes live weather integrity constraints.
def downgrade():
    """Remove live weather integrity constraints."""

    connection = op.get_bind()

    if connection.dialect.name == "sqlite":

        op.execute(
            "DROP TRIGGER IF EXISTS trg_weather_integrity_insert"
        )

        op.execute(
            "DROP TRIGGER IF EXISTS trg_weather_integrity_update"
        )

    elif connection.dialect.name == "postgresql":

        with op.batch_alter_table(
            "weather_records"
        ) as batch_op:

            batch_op.drop_constraint(
                "check_weather_latitude",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_weather_longitude",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_weather_rainfall",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_weather_wind_speed",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_weather_precipitation_interval",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_weather_source",
                type_="check"
            )
