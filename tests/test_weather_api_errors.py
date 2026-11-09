import pytest
import requests

from app import create_app
from app.config import TestingConfig
from app.services.weather_service import get_current_weather


@pytest.fixture
def app():
    return create_app(TestingConfig)


def test_weather_api_timeout(app, monkeypatch):
    def mock_get(*args, **kwargs):
        raise requests.Timeout("Connection timed out")

    monkeypatch.setattr(
        "app.services.weather_service.requests.get",
        mock_get
    )

    with app.app_context():
        with pytest.raises(RuntimeError, match="timed out"):
            get_current_weather(23.0225, 72.5714)


def test_weather_api_connection_error(app, monkeypatch):
    def mock_get(*args, **kwargs):
        raise requests.ConnectionError("Connection failed")

    monkeypatch.setattr(
        "app.services.weather_service.requests.get",
        mock_get
    )

    with app.app_context():
        with pytest.raises(RuntimeError, match="Unable to connect"):
            get_current_weather(23.0225, 72.5714)


def test_weather_api_http_error(app, monkeypatch):
    def mock_get(*args, **kwargs):
        response = requests.Response()
        response.status_code = 500
        raise requests.HTTPError("Server error", response=response)

    monkeypatch.setattr(
        "app.services.weather_service.requests.get",
        mock_get
    )

    with app.app_context():
        with pytest.raises(RuntimeError, match="HTTP error"):
            get_current_weather(23.0225, 72.5714)


def test_weather_api_general_request_error(app, monkeypatch):
    def mock_get(*args, **kwargs):
        raise requests.RequestException("Unexpected request failure")

    monkeypatch.setattr(
        "app.services.weather_service.requests.get",
        mock_get
    )

    with app.app_context():
        with pytest.raises(RuntimeError, match="request failed"):
            get_current_weather(23.0225, 72.5714)