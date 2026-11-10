# this file Saves weather observations to database
from datetime import datetime, timezone

from app.extensions import db
from app.models.weather_record import WeatherRecord


def save_weather_record(weather_data):
    """
    Save fetched weather information into the database.

    Args:
        weather_data (dict): Normalized weather data.

    Returns:
        WeatherRecord: The saved database record.
    """

    recorded_at = datetime.fromisoformat(
        weather_data["recorded_at"]
    )

    # Open-Meteo was requested to return UTC timestamps.
    # Attach UTC timezone if the timestamp has no timezone.
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)

    record = WeatherRecord(
        latitude=weather_data["latitude"],
        longitude=weather_data["longitude"],
        rainfall_mm=weather_data["rainfall_mm"],
        # Store the duration represented by the precipitation measurement.
          precipitation_interval_seconds=weather_data.get(
                "precipitation_interval_seconds"
            ),

        temperature_c=weather_data["temperature_c"],
        wind_speed_kmh=weather_data["wind_speed_kmh"],
        source=weather_data["source"],
        recorded_at=recorded_at
    )

    try:
        db.session.add(record)
        db.session.commit()

        return record

    except Exception:
        db.session.rollback()
        raise
