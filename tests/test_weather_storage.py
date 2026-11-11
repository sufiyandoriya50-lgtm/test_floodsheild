
import pytest

from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.weather_record import WeatherRecord
from app.services.weather_storage_service import save_weather_record


# Provides valid weather data for storage tests.
def valid_weather_data():
    """Return a valid weather observation for testing."""

    return {
        "latitude": 23.0225,
        "longitude": 72.5714,
        "rainfall_mm": 5.0,
        "precipitation_interval_seconds": 900,
        "temperature_c": 32.0,
        "wind_speed_kmh": 12.0,
        "source": "Open-Meteo",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


# Verifies that valid weather observations are saved correctly.
def test_save_weather_record_with_precipitation_interval(app):
    with app.app_context():
        record = save_weather_record(valid_weather_data())

        saved_record = db.session.get(WeatherRecord, record.id)

        assert saved_record is not None
        assert saved_record.precipitation_interval_seconds == 900
        assert saved_record.source == "Open-Meteo"


# Verifies that the precipitation interval can be omitted.
def test_save_weather_record_without_precipitation_interval(app):
    with app.app_context():
        weather_data = valid_weather_data()
        weather_data.pop("precipitation_interval_seconds")

        record = save_weather_record(weather_data)

        saved_record = db.session.get(WeatherRecord, record.id)

        assert saved_record is not None
        assert saved_record.precipitation_interval_seconds is None


# Verifies that invalid weather observations are rejected by the service.
@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("latitude", 91),
        ("longitude", 181),
        ("rainfall_mm", -1),
        ("wind_speed_kmh", -1),
        ("temperature_c", float("nan")),
        ("precipitation_interval_seconds", 0),
        ("precipitation_interval_seconds", -900),
        ("precipitation_interval_seconds", True),
        ("source", ""),
        ("source", "   "),
        ("source", "A" * 51),
    ],
)
def test_save_weather_record_rejects_invalid_data(
    app, field, invalid_value
):
    with app.app_context():
        weather_data = valid_weather_data()
        weather_data[field] = invalid_value

        with pytest.raises(ValueError):
            save_weather_record(weather_data)


# Verifies that database constraints reject invalid weather records.
@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("latitude", 91),
        ("longitude", 181),
        ("rainfall_mm", -1),
        ("wind_speed_kmh", -1),
        ("precipitation_interval_seconds", 0),
        ("source", "   "),
    ],
)
def test_weather_database_rejects_invalid_data(
    app, field, invalid_value
):
    with app.app_context():
        weather_data = valid_weather_data()
        weather_data[field] = invalid_value

        with pytest.raises(IntegrityError):
            db.session.execute(
                text("""
                    INSERT INTO weather_records (
                        latitude,
                        longitude,
                        rainfall_mm,
                        precipitation_interval_seconds,
                        temperature_c,
                        wind_speed_kmh,
                        source,
                        recorded_at
                    )
                    VALUES (
                        :latitude,
                        :longitude,
                        :rainfall_mm,
                        :precipitation_interval_seconds,
                        :temperature_c,
                        :wind_speed_kmh,
                        :source,
                        :recorded_at
                    )
                """),
                weather_data
            )

        db.session.rollback()
