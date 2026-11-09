from datetime import datetime, timezone

import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.historical_weather_record import HistoricalWeatherRecord
from app.services.historical_weather_storage_service import (
    create_historical_weather_record,
)


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_create_historical_weather_record(app):
    with app.app_context():

        recorded_at = datetime(
            2023, 7, 20, 10, 30,
            tzinfo=timezone.utc
        )

        record = create_historical_weather_record(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=45.0,
            recorded_at=recorded_at,
            source="Open-Meteo Archive",
            temperature_c=32.5,
            wind_speed_kmh=18.0,
            weather_code=61,
        )

        assert record.id is not None
        assert record.latitude == 23.0225
        assert record.longitude == 72.5714
        assert record.rainfall_mm == 45.0
        assert record.temperature_c == 32.5
        assert record.wind_speed_kmh == 18.0
        assert record.weather_code == 61
        assert record.source == "Open-Meteo Archive"

        saved_record = db.session.get(
            HistoricalWeatherRecord,
            record.id
        )

        assert saved_record is not None


def test_create_historical_weather_record_without_optional_fields(app):
    with app.app_context():

        record = create_historical_weather_record(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=20.0,
            recorded_at=datetime(
                2023, 8, 15, 8, 0,
                tzinfo=timezone.utc
            ),
            source="Historical Dataset",
        )

        assert record.id is not None
        assert record.temperature_c is None
        assert record.wind_speed_kmh is None
        assert record.weather_code is None

        assert HistoricalWeatherRecord.query.count() == 1

def test_invalid_weather_record_is_not_saved(app):
    with app.app_context():

        with pytest.raises(ValueError, match="Rainfall cannot be negative"):
            create_historical_weather_record(
                latitude=23.0225,
                longitude=72.5714,
                rainfall_mm=-10,
                recorded_at=datetime(
                    2023, 7, 20, 10, 30,
                    tzinfo=timezone.utc
                ),
                source="Open-Meteo Archive",
            )

        assert HistoricalWeatherRecord.query.count() == 0