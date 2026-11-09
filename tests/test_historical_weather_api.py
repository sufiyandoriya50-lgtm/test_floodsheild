
import pytest
from datetime import datetime, timezone

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.historical_weather_record import HistoricalWeatherRecord


@pytest.fixture
def weather_api_app():
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
        ])

        db.session.commit()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def weather_api_client(weather_api_app):
    return weather_api_app.test_client()


def test_get_all_historical_weather(weather_api_client):
    response = weather_api_client.get(
        "/api/historical-weather"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["pagination"]["total_records"] == 2
    assert len(data["data"]) == 2


def test_get_historical_weather_by_id(weather_api_client):
    response = weather_api_client.get(
        "/api/historical-weather/1"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["data"]["rainfall_mm"] == 25


def test_get_nonexistent_weather_record(weather_api_client):
    response = weather_api_client.get(
        "/api/historical-weather/99999"
    )

    assert response.status_code == 404


def test_filter_weather_by_date(weather_api_client):
    response = weather_api_client.get(
        "/api/historical-weather"
        "?start_date=2023-07-01"
        "&end_date=2023-07-20"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["pagination"]["total_records"] == 1


def test_filter_weather_by_location(weather_api_client):
    response = weather_api_client.get(
        "/api/historical-weather"
        "?latitude=23.0225"
        "&longitude=72.5714"
        "&radius_km=5"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["pagination"]["total_records"] == 2


def test_reject_incomplete_location_filter(weather_api_client):
    response = weather_api_client.get(
        "/api/historical-weather?latitude=23.0225"
    )

    assert response.status_code == 400


def test_reject_negative_radius(weather_api_client):
    response = weather_api_client.get(
        "/api/historical-weather"
        "?latitude=23.0225"
        "&longitude=72.5714"
        "&radius_km=-5"
    )

    assert response.status_code == 400


def test_historical_weather_pagination(weather_api_client):
    response = weather_api_client.get(
        "/api/historical-weather?page=1&per_page=1"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["pagination"]["total_records"] == 2
    assert data["pagination"]["per_page"] == 1
    assert len(data["data"]) == 1
