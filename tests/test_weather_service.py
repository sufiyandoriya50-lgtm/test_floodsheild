from app import create_app
from app.services.weather_service import get_current_weather


app = create_app()

with app.app_context():
    try:
        weather = get_current_weather(
            latitude=23.0225,
            longitude=72.5714
        )

        print("\n========== FLOODSHIELD WEATHER TEST ==========")

        print("Location:", weather["latitude"], weather["longitude"])
        print("Temperature:", weather["temperature_c"], "°C")
        print("Precipitation:", weather["rainfall_mm"], "mm")
        print("Wind Speed:", weather["wind_speed_kmh"], "km/h")
        print("Recorded At:", weather["recorded_at"])
        print("Source:", weather["source"])

        print("\nWeather service working successfully!")

    except Exception as error:
        print("\nWeather service test failed!")
        print("Error:", error)

def test_current_weather_extracts_precipitation_interval(app, monkeypatch):
    from app.services.weather_service import get_current_weather

    # Simulate an Open-Meteo response without making a real internet request.
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "current": {
                    "temperature_2m": 32.0,
                    "precipitation": 2.5,
                    "wind_speed_10m": 12.0,
                    "time": "2026-11-10T06:00",
                    "interval": 900,
                }
            }

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(
        "app.services.weather_service.requests.get",
        mock_get
    )

    with app.app_context():
        result = get_current_weather(23.0225, 72.5714)

    assert result["rainfall_mm"] == 2.5
    assert result["precipitation_interval_seconds"] == 900


def test_current_weather_missing_interval_returns_none(app, monkeypatch):
    from app.services.weather_service import get_current_weather

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "current": {
                    "temperature_2m": 32.0,
                    "precipitation": 2.5,
                    "wind_speed_10m": 12.0,
                    "time": "2026-11-10T06:00",
                }
            }

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(
        "app.services.weather_service.requests.get",
        mock_get
    )

    with app.app_context():
        result = get_current_weather(23.0225, 72.5714)

    assert result["precipitation_interval_seconds"] is None