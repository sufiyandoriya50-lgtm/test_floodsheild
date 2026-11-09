
from datetime import datetime, timezone

from app.models.historical_weather_record import HistoricalWeatherRecord


# These are initial data-review thresholds, not official weather limits.
SUSPICIOUS_RAINFALL_MM = 300
SUSPICIOUS_TEMPERATURE_HIGH_C = 55
SUSPICIOUS_TEMPERATURE_LOW_C = -50


"""
    Checks historical weather data and returns quality warnings.
    Does not automatically reject unusual but potentially genuine weather.
    """
def check_historical_weather_quality(
    latitude,
    longitude,
    rainfall_mm,
    recorded_at,
    source,
    temperature_c=None,
    wind_speed_kmh=None,
    exclude_record_id=None,
):

    warnings = []

    # Check whether rainfall is unusually high.
    if rainfall_mm > SUSPICIOUS_RAINFALL_MM:
        warnings.append("Suspiciously high rainfall measurement")

    # Check whether temperature is outside the initial review range.
    if temperature_c is not None:
        if temperature_c > SUSPICIOUS_TEMPERATURE_HIGH_C:
            warnings.append("Suspiciously high temperature")

        if temperature_c < SUSPICIOUS_TEMPERATURE_LOW_C:
            warnings.append("Suspiciously low temperature")

    # Check for missing optional measurements.
    if temperature_c is None:
        warnings.append("Temperature measurement is missing")

    if wind_speed_kmh is None:
        warnings.append("Wind speed measurement is missing")

    # Check whether the source is present.
    if not isinstance(source, str) or not source.strip():
        warnings.append("Weather data source is missing")

    # Check whether the observation time is in the future.
    if not isinstance(recorded_at, datetime):
        warnings.append("Observation timestamp must be a datetime")

    else:
       # SQLite may return a timezone-naive datetime even when the
       # original value was stored as timezone-aware UTC.
       if recorded_at.tzinfo is None or recorded_at.utcoffset() is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)

       # Compare timestamps consistently in UTC.
       if recorded_at.astimezone(timezone.utc) > datetime.now(timezone.utc):
           warnings.append("Observation timestamp is in the future")
    
    # Check whether another record already exists at this location and time.
    duplicate_query = HistoricalWeatherRecord.query.filter_by(
            latitude=latitude,
            longitude=longitude,
            recorded_at=recorded_at,
            )

    # Ignore the current record when checking an already-saved observation.
    if exclude_record_id is not None:
        duplicate_query = duplicate_query.filter(
            HistoricalWeatherRecord.id != exclude_record_id
        )

    duplicate = duplicate_query.first()

    if duplicate is not None:
        warnings.append("Possible duplicate weather observation")

    return {
        "is_valid": len(warnings) == 0,
        "warning_count": len(warnings),
        "warnings": warnings,
    }
