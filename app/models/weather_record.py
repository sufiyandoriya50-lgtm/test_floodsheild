
from datetime import datetime, timezone

from app.extensions import db


class WeatherRecord(db.Model):
    """
    Stores weather observations for FloodShield locations.
    """

    __tablename__ = "weather_records"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Geographic coordinates
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Weather measurements
    rainfall_mm = db.Column(db.Float, nullable=True)
    
    # Duration in seconds represented by the precipitation measurement.
    # Example: 900 means the precipitation value covers 15 minutes.
    precipitation_interval_seconds = db.Column(
    db.Integer,
    nullable=True
        )
    temperature_c = db.Column(db.Float, nullable=True)
    wind_speed_kmh = db.Column(db.Float, nullable=True)

    # Weather data provider
    source = db.Column(
        db.String(50),
        default="Open-Meteo",
        nullable=False
    )

    # Time of the actual weather observation
    recorded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    # Time this record was stored in our database
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return (
            f"<WeatherRecord {self.id}: "
            f"rainfall={self.rainfall_mm}mm>"
        )
