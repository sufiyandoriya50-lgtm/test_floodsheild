
from datetime import datetime, timezone
import math

from app.utils.geo import calculate_distance_km


# Initial engineering assumptions. These are not official flood standards.
DEFAULT_RADIUS_KM = 5.0

SEVERITY_SCORES = {
    "low": 20,
    "moderate": 45,
    "high": 70,
    "severe": 100,
}


"""
    Analyze historical flood events near a requested location.

    Nearby, more severe and more recent events contribute more
    strongly to the historical risk signal.
    """
def analyze_historical_flood_risk(
    historical_events,
    latitude,
    longitude,
    radius_km=DEFAULT_RADIUS_KM,
):

    def validate_coordinate(value, name, minimum, maximum):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not minimum <= value <= maximum
        ):
            raise ValueError(f"{name} is invalid")

    validate_coordinate(latitude, "Latitude", -90, 90)
    validate_coordinate(longitude, "Longitude", -180, 180)

    if (
        isinstance(radius_km, bool)
        or not isinstance(radius_km, (int, float))
        or not math.isfinite(radius_km)
        or radius_km <= 0
    ):
        raise ValueError("Radius must be a positive number")

    if not historical_events:
        return {
            "available": False,
            "score": None,
            "category": "insufficient_data",
            "nearby_events": 0,
            "message": "No historical flood events are available.",
        }

    now = datetime.now(timezone.utc)

    weighted_scores = []
    nearby_event_count = 0

    for event in historical_events:
        event_lat = event.latitude
        event_lon = event.longitude

        try:
            validate_coordinate(event_lat, "Event latitude", -90, 90)
            validate_coordinate(event_lon, "Event longitude", -180, 180)
        except ValueError:
            continue

        distance = calculate_distance_km(
            latitude,
            longitude,
            event_lat,
            event_lon,
        )

        if distance > radius_km:
            continue

        severity = (event.severity or "").strip().lower()

        if severity not in SEVERITY_SCORES:
            continue

        event_date = event.event_date

        if not isinstance(event_date, datetime):
            continue

        # SQLite may return naive UTC datetimes.
        if event_date.tzinfo is None:
            event_date = event_date.replace(tzinfo=timezone.utc)

        event_date = event_date.astimezone(timezone.utc)

        age_days = (now - event_date).total_seconds() / 86400

        # Exclude future-dated events.
        if age_days < 0:
            continue

        # Recent events receive more weight than older events.
        recency_weight = math.exp(-age_days / 3650)

        # Nearby events receive more weight than distant events.
        distance_weight = max(0.0, 1 - distance / radius_km)

        weight = recency_weight * distance_weight

        weighted_scores.append(
            (SEVERITY_SCORES[severity], weight)
        )

        nearby_event_count += 1

    if not weighted_scores:
        return {
            "available": False,
            "score": None,
            "category": "insufficient_data",
            "nearby_events": 0,
            "message": "No valid nearby historical flood events were found.",
        }

    total_weight = sum(weight for _, weight in weighted_scores)

    if total_weight <= 0:
        return {
            "available": False,
            "score": None,
            "category": "insufficient_data",
            "nearby_events": nearby_event_count,
            "message": "Historical event weights could not be calculated.",
        }

    score = round(
        sum(value * weight for value, weight in weighted_scores)
        / total_weight
    )

    if score < 25:
        category = "low"
    elif score < 50:
        category = "moderate"
    elif score < 75:
        category = "high"
    else:
        category = "severe"

    return {
        "available": True,
        "score": score,
        "category": category,
        "nearby_events": nearby_event_count,
        "search_radius_km": radius_km,
        "message": (
            "Historical flood risk signal calculated from "
            "nearby recorded flood events."
        ),
    }
