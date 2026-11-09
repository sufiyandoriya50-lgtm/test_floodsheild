
import pytest
from datetime import datetime, timezone

from app.extensions import db
from app.models.historical_weather_record import HistoricalWeatherRecord
from app.services.historical_weather_query_service import (
    get_historical_weather_record,
    get_historical_weather_records,
)



@pytest.fixture
def weather_app():
    from app import create_app
    from app.config import TestingConfig

    test_app = create_app(TestingConfig)

    with test_app.app_context():
        db.create_all()

        db.session.add_all([
            HistoricalWeatherRecord(
                latitude=23.0225,
                longitude=72.5714,
                rainfall_mm=25,
                temperature_c=29,
                wind_speed_kmh=12,
                recorded_at=datetime(
                    2023, 7, 20, 10, 30, tzinfo=timezone.utc
                ),
                source="Open-Meteo Archive",
            ),
            HistoricalWeatherRecord(
                latitude=23.0300,
                longitude=72.5800,
                rainfall_mm=40,
                temperature_c=27,
                wind_speed_kmh=15,
                recorded_at=datetime(
                    2023, 7, 21, 12, 0, tzinfo=timezone.utc
                ),
                source="Open-Meteo Archive",
            ),
            HistoricalWeatherRecord(
                latitude=22.0000,
                longitude=72.0000,
                rainfall_mm=10,
                temperature_c=30,
                wind_speed_kmh=8,
                recorded_at=datetime(
                    2023, 8, 5, 10, 0, tzinfo=timezone.utc
                ),
                source="Open-Meteo Archive",
            ),
        ])

        db.session.commit()

        yield test_app

        db.session.remove()
        db.drop_all()

def test_get_weather_record_by_id(weather_app):
    with weather_app.app_context():
        record = HistoricalWeatherRecord.query.first()

        result = get_historical_weather_record(record.id)

        assert result is not None
        assert result.id == record.id


def test_get_nonexistent_weather_record(weather_app):
    with weather_app.app_context():
        result = get_historical_weather_record(99999)

        assert result is None


def test_filter_weather_by_date_range(weather_app):
    with weather_app.app_context():
        result = get_historical_weather_records(
            start_date="2023-07-01",
            end_date="2023-07-31",
        )

        assert result.total == 2


def test_filter_weather_by_location(weather_app):
    with weather_app.app_context():
        result = get_historical_weather_records(
            latitude=23.0225,
            longitude=72.5714,
            radius_km=5,
        )

        assert result["total"] == 2


def test_location_filter_requires_all_parameters(weather_app):
    with weather_app.app_context():
        with pytest.raises(ValueError):
            get_historical_weather_records(
                latitude=23.0225,
                radius_km=5,
            )


def test_pagination(weather_app):
    with weather_app.app_context():
        result = get_historical_weather_records(
            page=1,
            per_page=1,
        )

        assert result.total == 3
        assert len(result.items) == 1


def test_invalid_date_is_rejected(weather_app):
    with weather_app.app_context():
        with pytest.raises(ValueError):
            get_historical_weather_records(
                start_date="not-a-date"
            )


def test_invalid_radius_is_rejected(weather_app):
    with weather_app.app_context():
        with pytest.raises(ValueError):
            get_historical_weather_records(
                latitude=23.0225,
                longitude=72.5714,
                radius_km=-5,
            )
