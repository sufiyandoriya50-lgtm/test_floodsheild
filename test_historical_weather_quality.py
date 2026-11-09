
import pytest

from datetime import datetime, timezone

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.historical_weather_record import HistoricalWeatherRecord

from app.services.historical_weather_quality_service import (
    check_historical_weather_quality,
)


@pytest.fixture
def quality_app():
    test_app = create_app(TestingConfig)

    with test_app.app_context():
        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()


def test_normal_weather_data_has_no_warnings(quality_app):
    with quality_app.app_context():
        result = check_historical_weather_quality(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=25,
            temperature_c=29,
            wind_speed_kmh=12,
            recorded_at=datetime(
                2023, 7, 20, 10, 30,
                tzinfo=timezone.utc,
            ),
            source="Open-Meteo Archive",
        )

        assert result["is_valid"] is True
        assert result["warning_count"] == 0


def test_suspicious_rainfall_is_flagged(quality_app):
    with quality_app.app_context():
        result = check_historical_weather_quality(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=350,
            temperature_c=29,
            wind_speed_kmh=12,
            recorded_at=datetime(
                2023, 7, 20, 10, 30,
                tzinfo=timezone.utc,
            ),
            source="Open-Meteo Archive",
        )

        assert result["is_valid"] is False
        assert "Suspiciously high rainfall measurement" in result["warnings"]


def test_missing_temperature_is_flagged(quality_app):
    with quality_app.app_context():
        result = check_historical_weather_quality(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=25,
            recorded_at=datetime(
                2023, 7, 20, 10, 30,
                tzinfo=timezone.utc,
            ),
            source="Open-Meteo Archive",
        )

        assert "Temperature measurement is missing" in result["warnings"]


def test_duplicate_observation_is_flagged(quality_app):
    with quality_app.app_context():
        recorded_at = datetime(
            2023, 7, 20, 10, 30,
            tzinfo=timezone.utc,
        )

        db.session.add(
            HistoricalWeatherRecord(
                latitude=23.0225,
                longitude=72.5714,
                rainfall_mm=25,
                temperature_c=29,
                wind_speed_kmh=12,
                recorded_at=recorded_at,
                source="Open-Meteo Archive",
            )
        )
        db.session.commit()

        result = check_historical_weather_quality(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=25,
            temperature_c=29,
            wind_speed_kmh=12,
            recorded_at=recorded_at,
            source="Open-Meteo Archive",
        )

        assert "Possible duplicate weather observation" in result["warnings"]


def test_future_timestamp_is_flagged(quality_app):
    with quality_app.app_context():
        future_time = datetime(
            2099, 1, 1, 10, 0,
            tzinfo=timezone.utc,
        )

        result = check_historical_weather_quality(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=25,
            temperature_c=29,
            wind_speed_kmh=12,
            recorded_at=future_time,
            source="Open-Meteo Archive",
        )

        assert "Observation timestamp is in the future" in result["warnings"]
