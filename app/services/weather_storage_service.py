
import math
from datetime import datetime, timezone

from app.extensions import db
from app.models.weather_record import WeatherRecord


# Validates and stores live weather observations in the database.
def save_weather_record(weather_data):
    """Validate and safely store a live weather observation."""

    if not isinstance(weather_data, dict):
        raise ValueError("Weather data must be a dictionary")

    # Validate geographic coordinates.
    latitude = weather_data.get("latitude")
    longitude = weather_data.get("longitude")

    for value, field_name in (
        (latitude, "Latitude"),
        (longitude, "Longitude"),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{field_name} must be a finite number")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    # Validate optional and required weather measurements.
    rainfall_mm = weather_data.get("rainfall_mm")
    wind_speed_kmh = weather_data.get("wind_speed_kmh")
    temperature_c = weather_data.get("temperature_c")

    for value, field_name, required in (
        (rainfall_mm, "Rainfall", True),
        (wind_speed_kmh, "Wind speed", True),
        (temperature_c, "Temperature", False),
    ):
        if value is None and not required:
            continue

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{field_name} must be a finite number")

    if rainfall_mm < 0:
        raise ValueError("Rainfall cannot be negative")

    if wind_speed_kmh < 0:
        raise ValueError("Wind speed cannot be negative")

    # Validate the precipitation measurement interval.
    interval_seconds = weather_data.get(
        "precipitation_interval_seconds"
    )

    if interval_seconds is not None:
        if (
            isinstance(interval_seconds, bool)
            or not isinstance(interval_seconds, int)
            or interval_seconds <= 0
        ):
            raise ValueError(
                "Precipitation interval must be a positive integer"
            )

    # Validate the weather data source.
    source = weather_data.get("source")

    if not isinstance(source, str) or not source.strip():
        raise ValueError("Weather source is required")

    if len(source.strip()) > 50:
        raise ValueError("Weather source cannot exceed 50 characters")

    # Validate and normalize the observation timestamp.
    recorded_at_value = weather_data.get("recorded_at")

    if not isinstance(recorded_at_value, str):
        raise ValueError("Weather timestamp must be text")

    try:
        recorded_at = datetime.fromisoformat(recorded_at_value)
    except ValueError as error:
        raise ValueError("Invalid weather timestamp") from error

    if recorded_at.tzinfo is None or recorded_at.utcoffset() is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    else:
        recorded_at = recorded_at.astimezone(timezone.utc)

    # Create a database record using validated values.
    record = WeatherRecord(
        latitude=latitude,
        longitude=longitude,
        rainfall_mm=rainfall_mm,
        precipitation_interval_seconds=interval_seconds,
        temperature_c=temperature_c,
        wind_speed_kmh=wind_speed_kmh,
        source=source.strip(),
        recorded_at=recorded_at
    )

    # Save safely and roll back if database operations fail.
    try:
        db.session.add(record)
        db.session.commit()

        return record

    except Exception:
        db.session.rollback()
        raise
