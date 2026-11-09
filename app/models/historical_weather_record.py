from datetime import datetime, timezone

from app.extensions import db


class HistoricalWeatherRecord(db.Model):
    __tablename__ = "historical_weather_records"

    id = db.Column(db.Integer, primary_key=True)

    # Geographic location of the weather observation.
    latitude = db.Column(db.Float, nullable=False, index=True)
    longitude = db.Column(db.Float, nullable=False, index=True)

    # Historical weather measurements.
    temperature_c = db.Column(db.Float, nullable=True)
    rainfall_mm = db.Column(db.Float, nullable=False)
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