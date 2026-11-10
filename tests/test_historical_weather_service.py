from datetime import datetime, timezone

import pytest

from app.services.historical_weather_service import (
    validate_historical_weather_record,
)


@pytest.fixture
def valid_weather_data():
    return {
        "latitude": 23.0225,
        "longitude": 72.5714,
        "rainfall_mm": 45.0,
        "recorded_at": datetime(
            2023, 7, 20, 10, 30,
            tzinfo=timezone.utc,
        ),
        "source": "Open-Meteo Archive",
        "temperature_c": 32.5,
        "wind_speed_kmh": 18.0,
        "weather_code": 61,
    }


def test_valid_weather_record(valid_weather_data):
    result = validate_historical_weather_record(
        **valid_weather_data
    )

    assert result["latitude"] == 23.0225
    assert result["longitude"] == 72.5714
    assert result["rainfall_mm"] == 45.0
    assert result["source"] == "Open-Meteo Archive"


def test_negative_rainfall_rejected(valid_weather_data):
    valid_weather_data["rainfall_mm"] = -10

    with pytest.raises(ValueError, match="Rainfall cannot be negative"):
        validate_historical_weather_record(**valid_weather_data)


def test_invalid_latitude_rejected(valid_weather_data):
    valid_weather_data["latitude"] = 100

    with pytest.raises(ValueError, match="Latitude must be between"):
        validate_historical_weather_record(**valid_weather_data)


def test_invalid_longitude_rejected(valid_weather_data):
    valid_weather_data["longitude"] = 200

    with pytest.raises(ValueError, match="Longitude must be between"):
        validate_historical_weather_record(**valid_weather_data)


def test_negative_wind_speed_rejected(valid_weather_data):
    valid_weather_data["wind_speed_kmh"] = -5

    with pytest.raises(ValueError, match="Wind speed cannot be negative"):
        validate_historical_weather_record(**valid_weather_data)


def test_timezone_required(valid_weather_data):
    valid_weather_data["recorded_at"] = datetime(2023, 7, 20, 10, 30)

    with pytest.raises(ValueError, match="must include a timezone"):
        validate_historical_weather_record(**valid_weather_data)


def test_source_required(valid_weather_data):
    valid_weather_data["source"] = "   "

    with pytest.raises(ValueError, match="Source is required"):
        validate_historical_weather_record(**valid_weather_data)


def test_nan_rainfall_rejected(valid_weather_data):
    valid_weather_data["rainfall_mm"] = float("nan")

    with pytest.raises(ValueError, match="must be finite"):
        validate_historical_weather_record(**valid_weather_data)
"""
   test        -   what it checks
   
Valid interval : Accepts 3600 seconds
Missing interval : Accepts unknown interval
Zero interval : Rejects invalid duration
Negative interval : Rejects invalid duration
Float interval : Requires integer seconds
"""
def test_valid_precipitation_interval():
    result = validate_historical_weather_record(
        latitude=23.0225,
        longitude=72.5714,
        rainfall_mm=8.0,
        recorded_at=datetime.now(timezone.utc),
        source="Open-Meteo",
        precipitation_interval_seconds=3600,
    )

    assert result["precipitation_interval_seconds"] == 3600


def test_missing_precipitation_interval():
    result = validate_historical_weather_record(
        latitude=23.0225,
        longitude=72.5714,
        rainfall_mm=8.0,
        recorded_at=datetime.now(timezone.utc),
        source="Open-Meteo",
    )

    assert result["precipitation_interval_seconds"] is None


def test_reject_zero_precipitation_interval():
    with pytest.raises(ValueError):
        validate_historical_weather_record(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=8.0,
            recorded_at=datetime.now(timezone.utc),
            source="Open-Meteo",
            precipitation_interval_seconds=0,
        )


def test_reject_negative_precipitation_interval():
    with pytest.raises(ValueError):
        validate_historical_weather_record(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=8.0,
            recorded_at=datetime.now(timezone.utc),
            source="Open-Meteo",
            precipitation_interval_seconds=-900,
        )


def test_reject_float_precipitation_interval():
    with pytest.raises(ValueError):
        validate_historical_weather_record(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=8.0,
            recorded_at=datetime.now(timezone.utc),
            source="Open-Meteo",
            precipitation_interval_seconds=900.5,
        )        