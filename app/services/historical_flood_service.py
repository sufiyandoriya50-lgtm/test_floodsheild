
import math
from datetime import datetime

from app.models.historical_flood_event import HistoricalFloodEvent


ALLOWED_SEVERITIES = {
    "low",
    "moderate",
    "high",
    "severe"
}


# Validates historical flood event information before database storage.
def validate_historical_flood_event(
    latitude,
    longitude,
    event_date,
    source,
    severity=None,
    water_depth_cm=None
):
    """Validate and normalize historical flood event information."""

    # Validate latitude.
    if isinstance(latitude, bool) or not isinstance(latitude, (int, float)):
        raise ValueError("Latitude must be a number")

    if not math.isfinite(latitude):
        raise ValueError("Latitude must be finite")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    # Validate longitude.
    if isinstance(longitude, bool) or not isinstance(longitude, (int, float)):
        raise ValueError("Longitude must be a number")

    if not math.isfinite(longitude):
        raise ValueError("Longitude must be finite")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    # Validate event date.
    if isinstance(event_date, str):
        try:
            event_date = datetime.fromisoformat(
                event_date.replace("Z", "+00:00")
            )
        except ValueError:
            raise ValueError("Invalid event date format")

    if not isinstance(event_date, datetime):
        raise ValueError("Event date must be a valid datetime")

    if event_date.tzinfo is None or event_date.utcoffset() is None:
        raise ValueError("Event date must include a valid timezone")

    # Validate source.
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Historical event source is required")

    source = source.strip()

    if len(source) > 100:
        raise ValueError("Historical event source cannot exceed 100 characters")

    # Validate severity.
    if severity is not None:
        if not isinstance(severity, str):
            raise ValueError("Severity must be text")

        severity = severity.strip().lower()

        if severity not in ALLOWED_SEVERITIES:
            raise ValueError(
                "Severity must be low, moderate, high or severe"
            )

    # Validate water depth.
    if water_depth_cm is not None:
        if isinstance(water_depth_cm, bool):
            raise ValueError("Water depth must be a number")

        if not isinstance(water_depth_cm, (int, float)):
            raise ValueError("Water depth must be a number")

        if not math.isfinite(water_depth_cm):
            raise ValueError("Water depth must be finite")

        if water_depth_cm < 0:
            raise ValueError("Water depth cannot be negative")

    return {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "event_date": event_date,
        "source": source,
        "severity": severity,
        "water_depth_cm": (
            float(water_depth_cm)
            if water_depth_cm is not None
            else None
        )
    }
