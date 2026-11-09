from datetime import datetime, timezone

from app.extensions import db


class HistoricalFloodEvent(db.Model):

    __tablename__ = "historical_flood_events"

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