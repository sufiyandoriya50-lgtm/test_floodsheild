
from datetime import datetime, timedelta, timezone
import math


# Initial engineering assumptions, not officially validated flood thresholds.
FRESH_DATA_MAX_AGE_HOURS = 3

# These are provisional rainfall intensity thresholds in mm/hour.
LOW_RAINFALL_MM_PER_HOUR = 2.5
MODERATE_RAINFALL_MM_PER_HOUR = 7.5
HIGH_RAINFALL_MM_PER_HOUR = 15.0
SEVERE_RAINFALL_MM_PER_HOUR = 30.0


"""
    Analyze recent precipitation observations for a location.

    Only observations with known measurement intervals and fresh,
    valid timestamps are used.

    Returns a normalized rainfall score from 0 to 100.
    """
def analyze_rainfall(weather_records, now=None):

    if now is None:
        now = datetime.now(timezone.utc)

    if not isinstance(now, datetime):
        raise ValueError("now must be a datetime")

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    now = now.astimezone(timezone.utc)

    if not weather_records:
        return {
            "available": False,
            "score": None,
            "category": "insufficient_data",
            "message": "No weather observations are available.",
            "observations_used": 0,
        }

    valid_observations = []
    rejected_observations = 0

    for record in weather_records:
        rainfall = record.rainfall_mm
        interval = record.precipitation_interval_seconds
        recorded_at = record.recorded_at

        if (
            isinstance(rainfall, bool)
            or not isinstance(rainfall, (int, float))
            or not math.isfinite(rainfall)
            or rainfall < 0
        ):
            rejected_observations += 1
            continue

        if (
            isinstance(interval, bool)
            or not isinstance(interval, int)
            or interval <= 0
        ):
            rejected_observations += 1
            continue

        if not isinstance(recorded_at, datetime):
            rejected_observations += 1
            continue

        # SQLite may return a naive datetime even when the model
        # declares timezone support. Treat stored UTC values as UTC.
        if recorded_at.tzinfo is None:
            recorded_at = recorded_at.replace(tzinfo=timezone.utc)

        recorded_at = recorded_at.astimezone(timezone.utc)

        age = now - recorded_at

        if age < timedelta(0):
            rejected_observations += 1
            continue

        if age > timedelta(hours=FRESH_DATA_MAX_AGE_HOURS):
            rejected_observations += 1
            continue

        rainfall_rate = rainfall / (interval / 3600)

        valid_observations.append({
            "rainfall_rate_mm_per_hour": rainfall_rate,
            "recorded_at": recorded_at,
        })

    if not valid_observations:
        return {
            "available": False,
            "score": None,
            "category": "insufficient_data",
            "message": "No fresh observations with valid measurement intervals are available.",
            "observations_used": 0,
            "observations_rejected": rejected_observations,
        }

    # Use the highest valid recent rate as a conservative initial signal.
    # Do not add overlapping precipitation intervals together.
    maximum_rate = max(
        item["rainfall_rate_mm_per_hour"]
        for item in valid_observations
    )

    if maximum_rate < LOW_RAINFALL_MM_PER_HOUR:
        score = 10
        category = "low"

    elif maximum_rate < MODERATE_RAINFALL_MM_PER_HOUR:
        score = 30
        category = "moderate"

    elif maximum_rate < HIGH_RAINFALL_MM_PER_HOUR:
        score = 55
        category = "high"

    elif maximum_rate < SEVERE_RAINFALL_MM_PER_HOUR:
        score = 80
        category = "severe"

    else:
        score = 100
        category = "severe"

    return {
        "available": True,
        "score": score,
        "category": category,
        "maximum_rainfall_rate_mm_per_hour": round(maximum_rate, 2),
        "observations_used": len(valid_observations),
        "observations_rejected": rejected_observations,
        "measurement": "precipitation",
        "message": (
            "Rainfall risk signal calculated from fresh observations "
            "with known measurement intervals."
        ),
    }
