
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint

from app.extensions import db


# Stores live weather observations and enforces database-level data integrity.
class WeatherRecord(db.Model):
    """Represents a live weather observation for a FloodShield location."""

    __tablename__ = "weather_records"

    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="check_weather_latitude"
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="check_weather_longitude"
        ),
        CheckConstraint(
            "rainfall_mm IS NULL OR rainfall_mm >= 0",
            name="check_weather_rainfall"
        ),
        CheckConstraint(
            "wind_speed_kmh IS NULL OR wind_speed_kmh >= 0",
            name="check_weather_wind_speed"
        ),
        CheckConstraint(
            "precipitation_interval_seconds IS NULL "
            "OR precipitation_interval_seconds > 0",
            name="check_weather_precipitation_interval"
        ),
        CheckConstraint(
            "length(trim(source)) > 0 AND length(source) <= 50",
            name="check_weather_source"
        ),
    )

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Geographic coordinates
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Weather measurements
    rainfall_mm = db.Column(db.Float, nullable=True)

    # Duration in seconds represented by the precipitation measurement.
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
