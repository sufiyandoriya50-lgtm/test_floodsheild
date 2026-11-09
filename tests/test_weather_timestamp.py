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


def test_valid_timestamp(app, monkeypatch):
    mock_weather_response(monkeypatch, valid_payload())

    with app.app_context():
        result = get_current_weather(23.0225, 72.5714)

    assert result["recorded_at"] == "2026-11-08T09:00"


def test_missing_timestamp(app, monkeypatch):
    payload = valid_payload()
    del payload["current"]["time"]

    mock_weather_response(monkeypatch, payload)

    with app.app_context():
        with pytest.raises(ValueError, match="Missing weather fields"):
            get_current_weather(23.0225, 72.5714)


def test_invalid_timestamp(app, monkeypatch):
    payload = valid_payload()
    payload["current"]["time"] = "not-a-date"

    mock_weather_response(monkeypatch, payload)

    with app.app_context():
        with pytest.raises(ValueError, match="timestamp"):
            get_current_weather(23.0225, 72.5714)


def test_non_string_timestamp(app, monkeypatch):
    payload = valid_payload()
    payload["current"]["time"] = 12345

    mock_weather_response(monkeypatch, payload)

    with app.app_context():
        with pytest.raises(ValueError, match="timestamp"):
            get_current_weather(23.0225, 72.5714)