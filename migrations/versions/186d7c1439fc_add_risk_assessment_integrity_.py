
"""add risk assessment integrity constraints

Revision ID: 186d7c1439fc
Revises: 844055430f69
"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = "186d7c1439fc"
down_revision = "844055430f69"
branch_labels = None
depends_on = None


# Adds database-level validation for risk assessments.
def upgrade():
    """Add integrity constraints to risk assessments."""

    connection = op.get_bind()

    # Check existing records before applying constraints.
    invalid_records = connection.execute(
        sa.text("""
            SELECT id
            FROM risk_assessments
            WHERE
                latitude IS NULL
                OR latitude < -90
                OR latitude > 90
                OR longitude IS NULL
                OR longitude < -180
                OR longitude > 180
                OR risk_level NOT IN (
                    'low',
                    'moderate',
                    'high',
                    'severe',
                    'insufficient_data'
                )
                OR risk_level IS NULL
                OR (
                    risk_score IS NOT NULL
                    AND (
                        risk_score < 0
                        OR risk_score > 100
                    )
                )
                OR (
                    data_completeness IS NOT NULL
                    AND (
                        data_completeness < 0
                        OR data_completeness > 100
                    )
                )
            LIMIT 10
        """)
    ).fetchall()

    if invalid_records:
        raise RuntimeError(
            "Cannot apply risk-assessment integrity constraints. "
            f"Invalid assessment IDs: {invalid_records}"
        )

    # Add SQLite triggers for INSERT and UPDATE operations.
    if connection.dialect.name == "sqlite":

        op.execute("""
            CREATE TRIGGER trg_risk_assessment_integrity_insert
            BEFORE INSERT ON risk_assessments
            FOR EACH ROW
            WHEN
                NEW.latitude IS NULL
                OR NEW.latitude < -90
                OR NEW.latitude > 90
                OR NEW.longitude IS NULL
                OR NEW.longitude < -180
                OR NEW.longitude > 180
                OR NEW.risk_level IS NULL
                OR NEW.risk_level NOT IN (
                    'low',
                    'moderate',
                    'high',
                    'severe',
                    'insufficient_data'
                )
                OR (
                    NEW.risk_score IS NOT NULL
                    AND (
                        NEW.risk_score < 0
                        OR NEW.risk_score > 100
                    )
                )
                OR (
                    NEW.data_completeness IS NOT NULL
                    AND (
                        NEW.data_completeness < 0
                        OR NEW.data_completeness > 100
                    )
                )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid risk assessment'
                );
            END;
        """)

        op.execute("""
            CREATE TRIGGER trg_risk_assessment_integrity_update
            BEFORE UPDATE ON risk_assessments
            FOR EACH ROW
            WHEN
                NEW.latitude IS NULL
                OR NEW.latitude < -90
                OR NEW.latitude > 90
                OR NEW.longitude IS NULL
                OR NEW.longitude < -180
                OR NEW.longitude > 180
                OR NEW.risk_level IS NULL
                OR NEW.risk_level NOT IN (
                    'low',
                    'moderate',
                    'high',
                    'severe',
                    'insufficient_data'
                )
                OR (
                    NEW.risk_score IS NOT NULL
                    AND (
                        NEW.risk_score < 0
                        OR NEW.risk_score > 100
                    )
                )
                OR (
                    NEW.data_completeness IS NOT NULL
                    AND (
                        NEW.data_completeness < 0
                        OR NEW.data_completeness > 100
                    )
                )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid risk assessment'
                );
            END;
        """)

    # Add native CHECK constraints for PostgreSQL.
    elif connection.dialect.name == "postgresql":

        with op.batch_alter_table(
            "risk_assessments"
        ) as batch_op:

            batch_op.create_check_constraint(
                "check_risk_assessment_latitude",
                "latitude >= -90 AND latitude <= 90"
            )

            batch_op.create_check_constraint(
                "check_risk_assessment_longitude",
                "longitude >= -180 AND longitude <= 180"
            )

            batch_op.create_check_constraint(
                "check_risk_assessment_level",
                "risk_level IN "
                "('low', 'moderate', 'high', 'severe', "
                "'insufficient_data')"
            )

            batch_op.create_check_constraint(
                "check_risk_assessment_score",
                "risk_score IS NULL OR "
                "(risk_score >= 0 AND risk_score <= 100)"
            )

            batch_op.create_check_constraint(
                "check_risk_assessment_completeness",
                "data_completeness IS NULL OR "
                "(data_completeness >= 0 AND "
                "data_completeness <= 100)"
            )


# Removes risk-assessment integrity constraints.
def downgrade():
    """Remove risk-assessment integrity constraints."""

    connection = op.get_bind()

    if connection.dialect.name == "sqlite":

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_risk_assessment_integrity_insert"
        )

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_risk_assessment_integrity_update"
        )

    elif connection.dialect.name == "postgresql":

        with op.batch_alter_table(
            "risk_assessments"
        ) as batch_op:

            batch_op.drop_constraint(
                "check_risk_assessment_latitude",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_risk_assessment_longitude",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_risk_assessment_level",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_risk_assessment_score",
                type_="check"
            )

            batch_op.drop_constraint(
                "check_risk_assessment_completeness",
                type_="check"
            )
