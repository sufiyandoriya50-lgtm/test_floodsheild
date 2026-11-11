
"""Add device token integrity constraints."""

from alembic import op
import sqlalchemy as sa


# Migration revision identifiers.
revision = "d4a5cd3bcf6c"
down_revision = "994475ac1aa2"
branch_labels = None
depends_on = None


# Validate existing device-token records before adding constraints.
def check_existing_device_tokens():
    """Reject migration if existing device-token records are invalid."""

    connection = op.get_bind()

    invalid_record = connection.execute(
        sa.text("""
            SELECT id
            FROM device_tokens
            WHERE platform NOT IN ('android', 'ios')
               OR (
                    token IS NOT NULL
                    AND (
                        length(trim(token)) = 0
                        OR length(token) > 512
                    )
               )
               OR (
                    fid IS NOT NULL
                    AND (
                        length(trim(fid)) = 0
                        OR length(fid) > 512
                    )
               )
               OR (
                    (token IS NULL OR length(trim(token)) = 0)
                    AND
                    (fid IS NULL OR length(trim(fid)) = 0)
               )
            LIMIT 1
        """)
    ).first()

    if invalid_record:
        raise RuntimeError(
            "Cannot apply device-token integrity migration. "
            f"Invalid device-token record found: {invalid_record[0]}"
        )


# Apply device-token integrity constraints.
def upgrade():
    """Enforce valid device platforms and registration identifiers."""

    check_existing_device_tokens()

    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":

        op.execute("""
            CREATE TRIGGER trg_device_tokens_integrity_insert
            BEFORE INSERT ON device_tokens
            FOR EACH ROW
            WHEN
                NEW.platform NOT IN ('android', 'ios')
                OR (
                    NEW.token IS NOT NULL
                    AND (
                        length(trim(NEW.token)) = 0
                        OR length(NEW.token) > 512
                    )
                )
                OR (
                    NEW.fid IS NOT NULL
                    AND (
                        length(trim(NEW.fid)) = 0
                        OR length(NEW.fid) > 512
                    )
                )
                OR (
                    (
                        NEW.token IS NULL
                        OR length(trim(NEW.token)) = 0
                    )
                    AND (
                        NEW.fid IS NULL
                        OR length(trim(NEW.fid)) = 0
                    )
                )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid device token integrity data'
                );
            END;
        """)

        op.execute("""
            CREATE TRIGGER trg_device_tokens_integrity_update
            BEFORE UPDATE ON device_tokens
            FOR EACH ROW
            WHEN
                NEW.platform NOT IN ('android', 'ios')
                OR (
                    NEW.token IS NOT NULL
                    AND (
                        length(trim(NEW.token)) = 0
                        OR length(NEW.token) > 512
                    )
                )
                OR (
                    NEW.fid IS NOT NULL
                    AND (
                        length(trim(NEW.fid)) = 0
                        OR length(NEW.fid) > 512
                    )
                )
                OR (
                    (
                        NEW.token IS NULL
                        OR length(trim(NEW.token)) = 0
                    )
                    AND (
                        NEW.fid IS NULL
                        OR length(trim(NEW.fid)) = 0
                    )
                )
            BEGIN
                SELECT RAISE(
                    ABORT,
                    'Invalid device token integrity data'
                );
            END;
        """)

    elif dialect == "postgresql":

        op.create_check_constraint(
            "check_device_token_platform",
            "device_tokens",
            "platform IN ('android', 'ios')"
        )

        op.create_check_constraint(
            "check_device_token_identifier",
            "device_tokens",
            """
            (
                token IS NOT NULL
                AND length(trim(token)) > 0
                AND length(token) <= 512
            )
            OR
            (
                fid IS NOT NULL
                AND length(trim(fid)) > 0
                AND length(fid) <= 512
            )
            """
        )

        op.create_check_constraint(
            "check_device_token_token",
            "device_tokens",
            """
            token IS NULL OR
            (length(trim(token)) > 0 AND length(token) <= 512)
            """
        )

        op.create_check_constraint(
            "check_device_token_fid",
            "device_tokens",
            """
            fid IS NULL OR
            (length(trim(fid)) > 0 AND length(fid) <= 512)
            """
        )

    else:
        raise RuntimeError(
            f"Unsupported database dialect: {dialect}"
        )


# Remove device-token integrity constraints.
def downgrade():
    """Remove device-token integrity constraints."""

    dialect = op.get_bind().dialect.name

    if dialect == "sqlite":

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_device_tokens_integrity_insert"
        )

        op.execute(
            "DROP TRIGGER IF EXISTS "
            "trg_device_tokens_integrity_update"
        )

    elif dialect == "postgresql":

        op.drop_constraint(
            "check_device_token_fid",
            "device_tokens",
            type_="check"
        )

        op.drop_constraint(
            "check_device_token_token",
            "device_tokens",
            type_="check"
        )

        op.drop_constraint(
            "check_device_token_identifier",
            "device_tokens",
            type_="check"
        )

        op.drop_constraint(
            "check_device_token_platform",
            "device_tokens",
            type_="check"
        )
