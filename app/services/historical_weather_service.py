import math
from datetime import datetime, timezone


"""
    Validates one historical weather observation before database storage.
    """
def validate_historical_weather_record(
    latitude,
    longitude,
    rainfall_mm,
    recorded_at,
    source,
    temperature_c=None,
    wind_speed_kmh=None,
    weather_code=None,
    precipitation_interval_seconds=None,
):

    def validate_number(value, field_name):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field_name} must be a number")

        if not math.isfinite(value):
            raise ValueError(f"{field_name} must be finite")

        return float(value)

    latitude = validate_number(latitude, "Latitude")
    longitude = validate_number(longitude, "Longitude")
    rainfall_mm = validate_number(rainfall_mm, "Rainfall")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    if rainfall_mm < 0:
        raise ValueError("Rainfall cannot be negative")

    if temperature_c is not None:
        temperature_c = validate_number(
            temperature_c,
            "Temperature"
        )

    if wind_speed_kmh is not None:
        wind_speed_kmh = validate_number(
            wind_speed_kmh,
            "Wind speed"
        )

        if wind_speed_kmh < 0:
            raise ValueError("Wind speed cannot be negative")

    if weather_code is not None:
        if isinstance(weather_code, bool) or not isinstance(weather_code, int):
            raise ValueError("Weather code must be an integer")

    if not isinstance(recorded_at, datetime):
        raise ValueError("Recorded time must be a datetime")

    if recorded_at.tzinfo is None or recorded_at.utcoffset() is None:
        raise ValueError("Recorded time must include a timezone")

    recorded_at = recorded_at.astimezone(timezone.utc)

    if not isinstance(source, str) or not source.strip():
        raise ValueError("Source is required")
    # Validate the precipitation measurement interval when supplied.
    if precipitation_interval_seconds is not None:
        if (
            isinstance(precipitation_interval_seconds, bool)
            or not isinstance(precipitation_interval_seconds, int)
        ):
            raise ValueError(
                "Precipitation interval must be an integer number of seconds"
            )
    
        if precipitation_interval_seconds <= 0:
            raise ValueError(
                "Precipitation interval must be greater than zero"
            )
    return {
        "latitude": latitude,
        "longitude": longitude,
        "rainfall_mm": rainfall_mm,
        "recorded_at": recorded_at,
        "source": source.strip(),
        "temperature_c": temperature_c,
        "wind_speed_kmh": wind_speed_kmh,
        "weather_code": weather_code,
         # Preserve the validated precipitation measurement interval.
        "precipitation_interval_seconds":   precipitation_interval_seconds,
    }