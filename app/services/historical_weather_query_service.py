
from datetime import datetime, timezone, timedelta

from app.extensions import db
from app.models.historical_weather_record import HistoricalWeatherRecord
from app.utils.geo import calculate_distance_km


def parse_weather_date(value, field_name):
    """
    Converts an ISO date or datetime string into a UTC datetime.
    """

    if value is None:
        return None

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    try:
        parsed_date = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        raise ValueError(
            f"{field_name} must be a valid ISO date or datetime"
        )

    # Date-only values and timezone-naive datetimes are treated as UTC.
    if parsed_date.tzinfo is None:
        parsed_date = parsed_date.replace(tzinfo=timezone.utc)

    return parsed_date.astimezone(timezone.utc)


"""
    Retrieves one historical weather record using its database ID.
    """
def get_historical_weather_record(record_id):

    return db.session.get(HistoricalWeatherRecord, record_id)


"""
    Retrieves historical weather records with optional date,
    location-radius filters and pagination.
    """
def get_historical_weather_records(
    latitude=None,
    longitude=None,
    radius_km=None,
    start_date=None,
    end_date=None,
    page=1,
    per_page=20,
):

    # Validate pagination.
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError("Page must be a positive integer")

    if (
        isinstance(per_page, bool)
        or not isinstance(per_page, int)
        or not 1 <= per_page <= 100
    ):
        raise ValueError("per_page must be between 1 and 100")

    # Convert date strings into UTC datetimes.
    end_date_input = end_date

    start_date = parse_weather_date(start_date, "start_date")
    end_date = parse_weather_date(end_date, "end_date")

    # A date-only end date includes the entire specified day.
    if end_date and len(end_date_input) == 10:
        end_date += timedelta(days=1)

    if start_date and end_date and start_date >= end_date:
        raise ValueError("start_date cannot be after end_date")

    # Location filters must be supplied together.
    location_values = (latitude, longitude, radius_km)

    if any(value is not None for value in location_values):
        if any(value is None for value in location_values):
            raise ValueError(
                "latitude, longitude and radius_km are all required"
            )

        for value, field_name in (
            (latitude, "Latitude"),
            (longitude, "Longitude"),
            (radius_km, "Radius"),
        ):
            if isinstance(value, bool):
                raise ValueError(f"{field_name} must be a number")

            try:
                number = float(value)
            except (TypeError, ValueError):
                raise ValueError(f"{field_name} must be a number")

            if number != number or number in (float("inf"), float("-inf")):
                raise ValueError(f"{field_name} must be finite")

            if field_name == "Latitude" and not -90 <= number <= 90:
                raise ValueError("Latitude must be between -90 and 90")

            if field_name == "Longitude" and not -180 <= number <= 180:
                raise ValueError("Longitude must be between -180 and 180")

            if field_name == "Radius" and number <= 0:
                raise ValueError("Radius must be greater than zero")

        latitude = float(latitude)
        longitude = float(longitude)
        radius_km = float(radius_km)

    # Start building the database query.
    query = HistoricalWeatherRecord.query

    if start_date:
        query = query.filter(
            HistoricalWeatherRecord.recorded_at >= start_date
        )

    if end_date:
        if len(end_date_input) == 10:
            query = query.filter(
                HistoricalWeatherRecord.recorded_at < end_date
            )
        else:
            query = query.filter(
                HistoricalWeatherRecord.recorded_at <= end_date
            )

    # Newest observations appear first.
    query = query.order_by(
        HistoricalWeatherRecord.recorded_at.desc()
    )

    # Without a location filter, use database pagination directly.
    if latitude is None:
        return query.paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )

    # With a location filter, calculate actual distance for each record.
    candidates = query.all()
    matching_records = []

    for record in candidates:
        distance = calculate_distance_km(
            latitude,
            longitude,
            record.latitude,
            record.longitude,
        )

        if distance <= radius_km:
            matching_records.append(record)

    # Apply pagination after filtering by distance.
    total = len(matching_records)
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    return {
        "items": matching_records[start_index:end_index],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }
