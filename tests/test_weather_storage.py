
from app import create_app
from app.extensions import db
from app.services.weather_service import get_current_weather
from app.services.weather_storage_service import save_weather_record
from app.models.weather_record import WeatherRecord

app = create_app()

with app.app_context():
    try:
        # Step 1: Fetch real weather data
        weather = get_current_weather(
            latitude=23.0225,
            longitude=72.5714
        )

        # Step 2: Save weather data into SQLite
        record = save_weather_record(weather)

        print("\n========== WEATHER STORAGE TEST ==========")
        print("Saved record ID:", record.id)
        print("Temperature:", record.temperature_c, "°C")
        print("Precipitation:", record.rainfall_mm, "mm")
        print("Wind speed:", record.wind_speed_kmh, "km/h")

        # Step 3: Retrieve the saved record
        saved_record = db.session.get(
            WeatherRecord,
            record.id
        )

        print("\n========== DATABASE VERIFICATION ==========")
        print("Record found:", saved_record is not None)

        if saved_record:
            print("Database record ID:", saved_record.id)
            print("Database source:", saved_record.source)

        print("\nWeather storage test successful!")

    except Exception as error:
        db.session.rollback()
        print("\nWeather storage test failed!")
        print("Error:", error)
