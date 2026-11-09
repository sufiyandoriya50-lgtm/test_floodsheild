import pytest
from unittest.mock import Mock

from app import create_app
from app.config import TestingConfig
from app.services.weather_service import get_current_weather


@pytest.fixture
def app():
    return create_app(TestingConfig)


def mock_weather_response(monkeypatch, payload):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload

    monkeypatch.setattr(
        "app.services.weather_service.requests.get",
        lambda *args, **kwargs: response
    )


def valid_payload():
    return {
        "current": {
            "temperature_2m": 30.5,
            "precipitation": 2.4,
            "wind_speed_10m": 12.0,
            "time": "2026-11-08T09:00"
        }
    }


def test_valid_weather_response(app, monkeypatch):
    mock_weather_response(monkeypatch, valid_payload())

    with app.app_context():
        result = get_current_weather(23.0225, 72.5714)

    assert result["temperature_c"] == 30.5
    assert result["rainfall_mm"] == 2.4
    assert result["wind_speed_kmh"] == 12.0


def test_missing_current_data(app, monkeypatch):
    mock_weather_response(monkeypatch, {})

    with app.app_context():
        with pytest.raises(ValueError):
            get_current_weather(23.0225, 72.5714)


def test_missing_precipitation(app, monkeypatch):
    payload = valid_payload()
    del payload["current"]["precipitation"]

    mock_weather_response(monkeypatch, payload)

    with app.app_context():
        with pytest.raises(ValueError, match="precipitation"):
            get_current_weather(23.0225, 72.5714)


def test_invalid_temperature_type(app, monkeypatch):
    payload = valid_payload()
    payload["current"]["temperature_2m"] = "hot"

    mock_weather_response(monkeypatch, payload)

    with app.app_context():
        with pytest.raises(ValueError, match="temperature_2m"):
            get_current_weather(23.0225, 72.5714)


def test_negative_precipitation(app, monkeypatch):
    payload = valid_payload()
    payload["current"]["precipitation"] = -5

    mock_weather_response(monkeypatch, payload)

    with app.app_context():
        with pytest.raises(ValueError, match="precipitation"):
            get_current_weather(23.0225, 72.5714)


def test_infinite_wind_speed(app, monkeypatch):
    payload = valid_payload()
    payload["current"]["wind_speed_10m"] = float("inf")

    mock_weather_response(monkeypatch, payload)

    with app.app_context():
        with pytest.raises(ValueError, match="wind_speed_10m"):
            get_current_weather(23.0225, 72.5714)