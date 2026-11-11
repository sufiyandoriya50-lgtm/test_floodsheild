
"""Add flood report integrity constraints.

Revision ID: b24e9fad9fd6
Revises: 2576d00da617
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers used by Alembic.
revision = "b24e9fad9fd6"
down_revision = "2576d00da617"
branch_labels = None
depends_on = None


# Adds database-level validation to flood reports.
def upgrade():

    connection = op.get_bind()
    dialect = connection.dialect.name

    # Reject migration if existing reports contain invalid values.
    invalid_report = connection.execute(
        sa.text("""
            SELECT id
            FROM flood_reports
            WHERE
                latitude < -90 OR latitude > 90
                OR longitude < -180 OR longitude > 180
                OR (
                    water_depth_cm IS NOT NULL
                    AND water_depth_cm < 0
                )
                OR status NOT IN ('pending', 'verified', 'rejected')
            LIMIT 1
        """)
    ).first()

    if invalid_report:
        raise RuntimeError(
            "Cannot add flood report constraints: "
            f"invalid report found (ID: {invalid_report[0]})."
        )

    # Use triggers on SQLite to avoid rebuilding the referenced table.
    if dialect == "sqlite":

        op.execute("""
            CREATE TRIGGER trg_flood_reports_integrity_insert
            BEFORE INSERT ON flood_reports
            FOR EACH ROW
            WHEN
                NEW.latitude < -90 OR NEW.latitude > 90
                OR NEW.longitude < -180 OR NEW.longitude > 180
                OR (
                    NEW.water_depth_cm IS NOT NULL
                    AND NEW.water_depth_cm < 0
                )
                OR NEW.status NOT IN ('pending', 'verified', 'rejected')
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid flood report data'
                );
            END;
        """)

        op.execute("""
            CREATE TRIGGER trg_flood_reports_integrity_update
            BEFORE UPDATE ON flood_reports
            FOR EACH ROW
            WHEN
                NEW.latitude < -90 OR NEW.latitude > 90
                OR NEW.longitude < -180 OR NEW.longitude > 180
                OR (
                    NEW.water_depth_cm IS NOT NULL
                    AND NEW.water_depth_cm < 0
                )
                OR NEW.status NOT IN ('pending', 'verified', 'rejected')
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid flood report data'
                );
            END;
        """)

    # Use native CHECK constraints on PostgreSQL.
    else:

        op.create_check_constraint(
            "check_flood_report_latitude",
            "flood_reports",
            "latitude >= -90 AND latitude <= 90"
        )

        op.create_check_constraint(
            "check_flood_report_longitude",
            "flood_reports",
            "longitude >= -180 AND longitude <= 180"
        )

        op.create_check_constraint(
            "check_flood_report_water_depth",
            "flood_reports",
            "water_depth_cm IS NULL OR water_depth_cm >= 0"
        )

        op.create_check_constraint(
            "check_flood_report_status",
            "flood_reports",
            "status IN ('pending', 'verified', 'rejected')"
        )


# Removes the flood report validation rules.
def downgrade():

    connection = op.get_bind()

    if connection.dialect.name == "sqlite":

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_flood_reports_integrity_update"
        )

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_flood_reports_integrity_insert"
        )

    else:

        op.drop_constraint(
            "check_flood_report_status",
            "flood_reports",
            type_="check"
        )

        op.drop_constraint(
            "check_flood_report_water_depth",
            "flood_reports",
            type_="check"
        )

        op.drop_constraint(
            "check_flood_report_longitude",
            "flood_reports",
            type_="check"
        )

        op.drop_constraint(
            "check_flood_report_latitude",
            "flood_reports",
            type_="check"
        )
