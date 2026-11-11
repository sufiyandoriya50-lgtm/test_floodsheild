
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint

from app.extensions import db


# Stores historical weather observations and enforces database-level data integrity.
class HistoricalWeatherRecord(db.Model):
    __tablename__ = "historical_weather_records"

    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="check_historical_weather_latitude"
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="check_historical_weather_longitude"
        ),
        CheckConstraint(
            "rainfall_mm >= 0",
            name="check_historical_weather_rainfall"
        ),
        CheckConstraint(
            "wind_speed_kmh IS NULL OR wind_speed_kmh >= 0",
            name="check_historical_weather_wind_speed"
        ),
        CheckConstraint(
            "precipitation_interval_seconds IS NULL "
            "OR precipitation_interval_seconds > 0",
            name="check_historical_weather_precipitation_interval"
        ),
        CheckConstraint(
            "length(trim(source)) > 0 AND length(source) <= 100",
            name="check_historical_weather_source"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    # Geographic location of the weather observation.
    latitude = db.Column(db.Float, nullable=False, index=True)
    longitude = db.Column(db.Float, nullable=False, index=True)

    # Historical weather measurements.
    temperature_c = db.Column(db.Float, nullable=True)
    rainfall_mm = db.Column(db.Float, nullable=False)

    # Duration in seconds represented by the precipitation measurement.
    precipitation_interval_seconds = db.Column(
        db.Integer,
        nullable=True
    )

    wind_speed_kmh = db.Column(db.Float, nullable=True)
    weather_code = db.Column(db.Integer, nullable=True)

    # Time when the weather observation was recorded.
    recorded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Origin of the historical weather data.
    source = db.Column(db.String(100), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<HistoricalWeatherRecord "
            f"{self.id}: {self.recorded_at}>"
        )
