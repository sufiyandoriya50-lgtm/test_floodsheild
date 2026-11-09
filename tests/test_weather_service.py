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
