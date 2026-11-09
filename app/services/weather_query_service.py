# This file Reads saved weather records from SQLite
from app.models.weather_record import WeatherRecord
from datetime import datetime, timezone


def get_latest_weather(latitude, longitude):
    """
    Retrieve the latest stored weather observation
    for a geographical location.
    """

    record = (
        WeatherRecord.query
        .filter_by(
            latitude=latitude,
            longitude=longitude
        )
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )

    if record is None:
        return None

    return {
        "id": record.id,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "rainfall_mm": record.rainfall_mm,
        "temperature_c": record.temperature_c,
        "wind_speed_kmh": record.wind_speed_kmh,
        "source": record.source,
        "recorded_at": record.recorded_at.isoformat()
    }

def get_weather_history(latitude, longitude, limit=24):
    records = (
        WeatherRecord.query
        .filter_by(
            latitude=latitude,
            longitude=longitude
        )
        .order_by(WeatherRecord.recorded_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": record.id,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "rainfall_mm": record.rainfall_mm,
            "temperature_c": record.temperature_c,
            "wind_speed_kmh": record.wind_speed_kmh,
            "source": record.source,
            "recorded_at": record.recorded_at.isoformat()
        }
        for record in records
    ]
def get_weather_history_by_date(
    latitude,
    longitude,
    start_date,
    end_date
):
    start_datetime = datetime.fromisoformat(start_date)
    end_datetime = datetime.fromisoformat(end_date)

    if start_datetime.tzinfo is None:
        start_datetime = start_datetime.replace(tzinfo=timezone.utc)

    if end_datetime.tzinfo is None:
        end_datetime = end_datetime.replace(tzinfo=timezone.utc)

    records = (
        WeatherRecord.query
        .filter(
            WeatherRecord.latitude == latitude,
            WeatherRecord.longitude == longitude,
            WeatherRecord.recorded_at >= start_datetime,
            WeatherRecord.recorded_at <= end_datetime
        )
        .order_by(WeatherRecord.recorded_at.asc())
        .all()
    )

    return [
        {
            "id": record.id,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "rainfall_mm": record.rainfall_mm,
            "temperature_c": record.temperature_c,
            "wind_speed_kmh": record.wind_speed_kmh,
            "source": record.source,
            "recorded_at": record.recorded_at.isoformat()
        }
        for record in records
    ]