
import pytest
from datetime import datetime, timezone

from app import create_app
from app.config import TestingConfig
from app.extensions import db

from app.models.historical_flood_event import HistoricalFloodEvent
from app.models.historical_weather_record import HistoricalWeatherRecord

from app.services.historical_weather_storage_service import (
    create_historical_weather_record,
)

from app.services.historical_weather_query_service import (
    get_historical_weather_records,
)

from app.services.historical_weather_quality_service import (
    check_historical_weather_quality,
)


@pytest.fixture
def integration_app():
    test_app = create_app(TestingConfig)

    with test_app.app_context():
        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()


def test_weather_storage_quality_and_retrieval(integration_app):
    with integration_app.app_context():

        # 1. Store a historical weather observation.
        record = create_historical_weather_record(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=45,
            temperature_c=28,
            wind_speed_kmh=12,
            recorded_at=datetime(
                2023, 7, 20, 10, 30,
                tzinfo=timezone.utc,
            ),
            source="Open-Meteo Archive",
        )

        assert record.id is not None

        # 2. Check the stored observation's quality.
        quality = check_historical_weather_quality(
            latitude=record.latitude,
            longitude=record.longitude,
            rainfall_mm=record.rainfall_mm,
            temperature_c=record.temperature_c,
            wind_speed_kmh=record.wind_speed_kmh,
            recorded_at=record.recorded_at,
            source=record.source,
            exclude_record_id=record.id,
        )
        print("\nQUALITY CHECK RESULT:", quality)
        print("STORED TIMESTAMP:", record.recorded_at)
        print("TIMESTAMP TIMEZONE:", record.recorded_at.tzinfo)

        assert quality["is_valid"] is True

        # 3. Retrieve the observation through the query service.
        result = get_historical_weather_records(
            start_date="2023-07-01",
            end_date="2023-07-31",
        )

        assert result.total == 1
        assert result.items[0].id == record.id


def test_duplicate_weather_is_detected(integration_app):
    with integration_app.app_context():

        recorded_at = datetime(
            2023, 7, 20, 10, 30,
            tzinfo=timezone.utc,
        )

        # Store the first observation.
        create_historical_weather_record(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=45,
            temperature_c=28,
            wind_speed_kmh=12,
            recorded_at=recorded_at,
            source="Open-Meteo Archive",
        )

        # Check the same observation again.
        quality = check_historical_weather_quality(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=45,
            temperature_c=28,
            wind_speed_kmh=12,
            recorded_at=recorded_at,
            source="Open-Meteo Archive",
        )

        assert "Possible duplicate weather observation" in quality["warnings"]


def test_historical_flood_and_weather_data_coexist(integration_app):
    with integration_app.app_context():

        # Insert a historical flood event.
        flood = HistoricalFloodEvent(
            event_name="Ahmedabad Historical Flood",
            latitude=23.0225,
            longitude=72.5714,
            event_date=datetime(
                2023, 7, 20, 10, 30,
                tzinfo=timezone.utc,
            ),
            water_depth_cm=40,
            severity="high",
            description="Historical waterlogging event",
            source="Official Dataset",
        )

        # Insert a weather observation for the same location and time.
        weather = HistoricalWeatherRecord(
            latitude=23.0225,
            longitude=72.5714,
            rainfall_mm=45,
            temperature_c=28,
            wind_speed_kmh=12,
            recorded_at=datetime(
                2023, 7, 20, 10, 30,
                tzinfo=timezone.utc,
            ),
            source="Open-Meteo Archive",
        )

        db.session.add_all([flood, weather])
        db.session.commit()

        # Confirm both types of historical information are stored.
        assert HistoricalFloodEvent.query.count() == 1
        assert HistoricalWeatherRecord.query.count() == 1

        assert flood.latitude == weather.latitude
        assert flood.longitude == weather.longitude
