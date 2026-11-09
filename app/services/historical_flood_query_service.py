from datetime import datetime , timezone , timedelta

from app.models.historical_flood_event import HistoricalFloodEvent
from app.utils.geo import calculate_distance_km
from app.extensions import db


ALLOWED_SEVERITIES = {
    "low",
    "moderate",
    "high",
    "severe"
}


def parse_event_date(value, field_name):
    """
    Converts an ISO date or datetime string into a timezone-aware datetime.
    """

    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a date string")

    try:
        # Accept a date such as 2023-07-22 as well as an ISO datetime.
        if len(value) == 10:
            parsed_date = datetime.fromisoformat(value)
        else:
            parsed_date = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

    except ValueError:
        raise ValueError(
            f"{field_name} must use ISO format"
        )

    # Treat date-only values as UTC midnight.
    if parsed_date.tzinfo is None:
        parsed_date = parsed_date.replace(tzinfo=timezone.utc)

    return parsed_date.astimezone(timezone.utc)


def get_historical_flood_event(event_id):
    """
    Retrieves one historical flood event using its ID.
    """

    return db.session.get(HistoricalFloodEvent, event_id)

"""
    Retrieves one historical flood event using its ID.
    """
def get_historical_flood_event(event_id):

    return db.session.get(HistoricalFloodEvent, event_id)


"""
    Retrieves historical flood events using optional filters.
    Supports severity, date range, location and pagination.
    """
def get_all_historical_flood_events(
    severity=None,
    start_date=None,
    end_date=None,
    latitude=None,
    longitude=None,
    radius_km=None,
    page=1,
    per_page=20
):

    # Validate pagination
    if (
        isinstance(page, bool)
        or not isinstance(page, int)
        or page < 1
    ):
        raise ValueError("Page must be a positive integer")

    if (
        isinstance(per_page, bool)
        or not isinstance(per_page, int)
        or not 1 <= per_page <= 100
    ):
        raise ValueError("per_page must be between 1 and 100")

    # Validate severity
    if severity is not None:
        if not isinstance(severity, str):
            raise ValueError("Severity must be text")

        severity = severity.strip().lower()

        if severity not in ALLOWED_SEVERITIES:
            raise ValueError(
                "Severity must be low, moderate, high or severe"
            )
    # Preserve the original end date to determine whether it is date-only.
    end_date_input = end_date

    # Convert date strings into timezone-aware datetime objects.
    start_date = parse_event_date(start_date, "start_date")
    end_date = parse_event_date(end_date, "end_date")

    # If the end date is date-only, move it to the next day's midnight.
    if end_date and len(end_date_input) == 10:
       end_date += timedelta(days=1)

    # Ensure the start date is not after the end date.
    if start_date and end_date and start_date >= end_date:
       raise ValueError("start_date cannot be after end_date") 
    if start_date and end_date and start_date > end_date:
        raise ValueError("start_date cannot be after end_date")

    # Validate location filters
    location_values = [latitude, longitude, radius_km]

    location_filter_used = any(
        value is not None for value in location_values
    )

    if location_filter_used and any(
        value is None for value in location_values
    ):
        raise ValueError(
            "Latitude, longitude and radius_km are all required"
        )

    if location_filter_used:
        for value in (latitude, longitude, radius_km):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("Location values must be numbers")

        if not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")

        if not -180 <= longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")

        if radius_km <= 0:
            raise ValueError("Radius must be greater than zero")

    # Build database query
    query = HistoricalFloodEvent.query

    if severity:
        query = query.filter(
            HistoricalFloodEvent.severity == severity
        )

    if start_date:
        query = query.filter(
            HistoricalFloodEvent.event_date >= start_date
        )

    if end_date:
        query = query.filter(
            HistoricalFloodEvent.event_date < end_date
        )

    query = query.order_by(
        HistoricalFloodEvent.event_date.desc()
    )

    # Use normal database pagination when location filtering is not needed.
    if not location_filter_used:
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    # Location filtering: calculate distance for each date/severity candidate.
    events = query.all()

    nearby_events = []

    for event in events:
        distance = calculate_distance_km(
            latitude,
            longitude,
            event.latitude,
            event.longitude
        )

        if distance <= radius_km:
            nearby_events.append(event)

    total = len(nearby_events)

    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    return {
        "items": nearby_events[start_index:end_index],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }