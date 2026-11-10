from app.extensions import db
from app.models.historical_weather_record import HistoricalWeatherRecord
from app.services.historical_weather_service import (
    validate_historical_weather_record,
)


"""
    Validates and stores one historical weather observation.
    """
def create_historical_weather_record(
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

    # Step 1: Validate all incoming weather data.
    validated_data = validate_historical_weather_record(
        latitude=latitude,
        longitude=longitude,
        rainfall_mm=rainfall_mm,
        recorded_at=recorded_at,
        source=source,
        temperature_c=temperature_c,
        wind_speed_kmh=wind_speed_kmh,
        weather_code=weather_code,
        precipitation_interval_seconds=precipitation_interval_seconds,
    )

    # Step 2: Create a database model using validated values.
    record = HistoricalWeatherRecord(**validated_data)

    # Step 3: Save the record safely.
    try:
        db.session.add(record)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return record