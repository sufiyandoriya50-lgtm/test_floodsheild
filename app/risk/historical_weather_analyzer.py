
from datetime import datetime, timedelta, timezone
import math

from app.utils.geo import calculate_distance_km


# Initial analysis window: the previous 30 days.
HISTORICAL_WEATHER_WINDOW_DAYS = 30

# Provisional precipitation intensity thresholds in mm/hour.
LOW_INTENSITY = 2.5
MODERATE_INTENSITY = 7.5
HIGH_INTENSITY = 15.0
SEVERE_INTENSITY = 30.0


"""
    Analyzes historical precipitation observations near a location.

    This provides historical weather context. It is not an
    additional weighted factor in the combined risk score.
    """
def analyze_historical_weather(
    records,
    latitude,
    longitude,
    radius_km=5.0,
    now=None,
):

    # Validate the assessment time.
    if now is None:
        now = datetime.now(timezone.utc)

    if not isinstance(now, datetime):
        raise ValueError("now must be a datetime")

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    now = now.astimezone(timezone.utc)

    # Validate location and search radius.
    for value, name in (
        (latitude, "Latitude"),
        (longitude, "Longitude"),
        (radius_km, "Radius"),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{name} must be a finite number")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    if radius_km <= 0:
        raise ValueError("Radius must be greater than zero")

    if not records:
        return {
            "available": False,
            "category": "insufficient_data",
            "observations_used": 0,
            "message": "No historical weather records are available.",
        }

    window_start = now - timedelta(
        days=HISTORICAL_WEATHER_WINDOW_DAYS
    )

    valid_rates = []
    rejected_records = 0

    for record in records:
        rainfall = record.rainfall_mm
        interval = record.precipitation_interval_seconds
        recorded_at = record.recorded_at

        # Validate precipitation amount.
        if (
            isinstance(rainfall, bool)
            or not isinstance(rainfall, (int, float))
            or not math.isfinite(rainfall)
            or rainfall < 0
        ):
            rejected_records += 1
            continue

        # A known measurement interval is necessary
        # to calculate precipitation intensity.
        if (
            isinstance(interval, bool)
            or not isinstance(interval, int)
            or interval <= 0
        ):
            rejected_records += 1
            continue

        if not isinstance(recorded_at, datetime):
            rejected_records += 1
            continue

        # SQLite may return naive UTC timestamps.
        if recorded_at.tzinfo is None:
            recorded_at = recorded_at.replace(
                tzinfo=timezone.utc
            )

        recorded_at = recorded_at.astimezone(timezone.utc)

        # Exclude observations outside the analysis window.
        if recorded_at < window_start or recorded_at > now:
            rejected_records += 1
            continue

        # Validate the record's location.
        record_latitude = record.latitude
        record_longitude = record.longitude

        try:
            distance = calculate_distance_km(
                latitude,
                longitude,
                record_latitude,
                record_longitude,
            )
        except (TypeError, ValueError):
            rejected_records += 1
            continue

        if distance > radius_km:
            rejected_records += 1
            continue

        # Convert precipitation into an hourly rate.
        rate = rainfall / (interval / 3600)

        valid_rates.append(rate)

    if not valid_rates:
        return {
            "available": False,
            "category": "insufficient_data",
            "observations_used": 0,
            "observations_rejected": rejected_records,
            "message": (
                "No valid historical precipitation observations "
                "were found in the selected area and time window."
            ),
        }

    maximum_rate = max(valid_rates)
    average_rate = sum(valid_rates) / len(valid_rates)

    if maximum_rate < LOW_INTENSITY:
        intensity = "low"
    elif maximum_rate < MODERATE_INTENSITY:
        intensity = "moderate"
    elif maximum_rate < HIGH_INTENSITY:
        intensity = "high"
    else:
        intensity = "severe"

    return {
        "available": True,
        "category": intensity,
        "maximum_precipitation_rate_mm_per_hour": round(
            maximum_rate, 2
        ),
        "average_precipitation_rate_mm_per_hour": round(
            average_rate, 2
        ),
        "observations_used": len(valid_rates),
        "observations_rejected": rejected_records,
        "analysis_window_days": HISTORICAL_WEATHER_WINDOW_DAYS,
        "message": (
            "Historical precipitation context calculated from "
            "valid observations within the selected area."
        ),
    }
