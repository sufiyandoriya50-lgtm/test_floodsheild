from datetime import datetime

from app.models.historical_flood_event import HistoricalFloodEvent


ALLOWED_SEVERITIES = {
    "low",
    "moderate",
    "high",
    "severe"
}


"""
Validates historical flood event information
before it is stored in the database.
"""
def validate_historical_flood_event(
    latitude,
    longitude,
    event_date,
    source,
    severity=None,
    water_depth_cm=None
):

    # Validate latitude
    if isinstance(latitude, bool) or not isinstance(latitude, (int, float)):
        raise ValueError("Latitude must be a number")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    # Validate longitude
    if isinstance(longitude, bool) or not isinstance(longitude, (int, float)):
        raise ValueError("Longitude must be a number")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    # Validate event date
    if isinstance(event_date, str):
        try:
            event_date = datetime.fromisoformat(
                event_date.replace("Z", "+00:00")
            )
        except ValueError:
            raise ValueError("Invalid event date format")

    if not isinstance(event_date, datetime):
        raise ValueError("Event date must be a valid datetime")

    if event_date.tzinfo is None:
        raise ValueError("Event date must include a timezone")

    # Validate source
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Historical event source is required")

    # Validate severity
    if severity is not None:
        if not isinstance(severity, str):
            raise ValueError("Severity must be text")

        severity = severity.strip().lower()

        if severity not in ALLOWED_SEVERITIES:
            raise ValueError(
                "Severity must be low, moderate, high or severe"
            )

    # Validate water depth
    if water_depth_cm is not None:
        if isinstance(water_depth_cm, bool):
            raise ValueError("Water depth must be a number")

        if not isinstance(water_depth_cm, (int, float)):
            raise ValueError("Water depth must be a number")

        if water_depth_cm < 0:
            raise ValueError("Water depth cannot be negative")

    return {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "event_date": event_date,
        "source": source.strip(),
        "severity": severity,
        "water_depth_cm": (
            float(water_depth_cm)
            if water_depth_cm is not None
            else None
        )
    }