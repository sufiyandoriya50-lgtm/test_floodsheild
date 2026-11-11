
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint

from app.extensions import db


# Stores historical flood events and enforces database-level data integrity.
class HistoricalFloodEvent(db.Model):
    """Represents a recorded historical flood event."""

    __tablename__ = "historical_flood_events"

    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="check_historical_flood_latitude"
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="check_historical_flood_longitude"
        ),
        CheckConstraint(
            "water_depth_cm IS NULL OR water_depth_cm >= 0",
            name="check_historical_flood_water_depth"
        ),
        CheckConstraint(
            "severity IS NULL OR severity IN "
            "('low', 'moderate', 'high', 'severe')",
            name="check_historical_flood_severity"
        ),
        CheckConstraint(
            "length(trim(source)) > 0 AND length(source) <= 100",
            name="check_historical_flood_source"
        ),
        CheckConstraint(
            "event_name IS NULL OR "
            "(length(trim(event_name)) > 0 AND length(event_name) <= 150)",
            name="check_historical_flood_event_name"
        ),
        CheckConstraint(
            "source_reference IS NULL OR "
            "(length(trim(source_reference)) > 0 "
            "AND length(source_reference) <= 500)",
            name="check_historical_flood_source_reference"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    event_name = db.Column(
        db.String(150),
        nullable=True
    )

    latitude = db.Column(
        db.Float,
        nullable=False,
        index=True
    )

    longitude = db.Column(
        db.Float,
        nullable=False,
        index=True
    )

    event_date = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True
    )

    water_depth_cm = db.Column(
        db.Float,
        nullable=True
    )

    severity = db.Column(
        db.String(20),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    source = db.Column(
        db.String(100),
        nullable=False
    )

    source_reference = db.Column(
        db.String(500),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return (
            f"<HistoricalFloodEvent "
            f"{self.id}: {self.event_name}>"
        )
