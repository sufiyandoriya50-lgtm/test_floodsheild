# This file Fetches live weather from Open-Meteo
import requests
import math
from flask import current_app
from datetime import datetime

from app.services.weather_storage_service import save_weather_record
from app.services.weather_query_service import get_latest_weather
from app.services.weather_query_service import get_weather_history_by_date


# To check if given coordinates are valid or invalid
def validate_coordinates(latitude, longitude):
    """
    Validate geographical coordinates.

    Latitude must be between -90 and 90.
    Longitude must be between -180 and 180.
    """
    # Reject Boolean values explicitly.
    if isinstance(latitude, bool):
        raise ValueError("Latitude must be a number")

    if isinstance(longitude, bool):
        raise ValueError("Longitude must be a number")
    # Check numeric types.
    if not isinstance(latitude, (int, float)):
        raise ValueError("Latitude must be a number")

    if not isinstance(longitude, (int, float)):
        raise ValueError("Longitude must be a number")
    # Reject NaN and infinity.
    if not math.isfinite(latitude):
        raise ValueError("Latitude must be a finite number")

    if not math.isfinite(longitude):
        raise ValueError("Longitude must be a finite number")
    # Check geographical boundaries.
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")


"""it  
gets actual weather data from external source 
Rejects invalid locations before making requests
Timeout handling,
Identifies network failures,
Detects unsuccessful API responses,
Rejects invalid responses,
Prevents incomplete weather records,    """
# Fetches and validates current weather data from Open-Meteo.


def get_current_weather(latitude, longitude):
    """
    Fetch current weather data from the Open-Meteo API.

    Args:
        latitude (float): Location latitude.
        longitude (float): Location longitude.

    Returns:
        dict: Normalized current weather information.

    Raises:
        requests.RequestException: If the API request fails.
        ValueError: If the API response is invalid.
    """

    validate_coordinates(latitude, longitude)  # funtion inherited from above

    api_url = current_app.config["WEATHER_API_URL"]

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "precipitation", "wind_speed_10m"],
        "timezone": "UTC",
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)

        response.raise_for_status()

        data = response.json()

    except requests.Timeout as error:
        raise RuntimeError("Weather API request timed out") from error

    except requests.ConnectionError as error:
        raise RuntimeError("Unable to connect to weather API") from error

    except requests.HTTPError as error:
        raise RuntimeError("Weather API returned an HTTP error") from error

    except requests.RequestException as error:
        raise RuntimeError("Weather API request failed") from error

    except ValueError as error:
        raise RuntimeError("Weather API returned invalid JSON") from error

    # Validate that the API returned a usable current weather object.
    current = data.get("current")
    
    if not isinstance(current, dict) or not current:
        raise ValueError("Weather API response is missing current weather data")
    
   # Validate the precipitation measurement interval when supplied.
    interval_seconds = current.get("interval")
    
    if interval_seconds is not None:
        if (
            isinstance(interval_seconds, bool)
            or not isinstance(interval_seconds, int)
            or interval_seconds <= 0
        ):
            raise ValueError(
                "Invalid precipitation measurement interval"
            )
    # STEP 1: Check required fields
    required_fields = ["temperature_2m", "precipitation", "wind_speed_10m", "time"]

    missing_fields = [field for field in required_fields if current.get(field) is None]

    if missing_fields:
        raise ValueError(f"Missing weather fields: {', '.join(missing_fields)}")

    # STEP 2: Validate numeric weather values
    numeric_fields = ["temperature_2m", "precipitation", "wind_speed_10m"]

    for field in numeric_fields:
        value = current[field]

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Invalid numeric value for {field}")

        if not math.isfinite(value):
            raise ValueError(f"Invalid numeric value for {field}")

        if value < 0 and field != "temperature_2m":
            raise ValueError(f"{field} cannot be negative")
        
    # Validate weather timestamp
    recorded_at = current["time"]

    if not isinstance(recorded_at, str):
        raise ValueError("Invalid weather timestamp")

    try:
        datetime.fromisoformat(recorded_at)
    except ValueError as error:
        raise ValueError("Invalid weather timestamp format") from error
    return {
    "latitude": latitude,
    "longitude": longitude,
    "temperature_c": current["temperature_2m"],
    "rainfall_mm": current["precipitation"],
    "precipitation_interval_seconds": interval_seconds,
    "wind_speed_kmh": current["wind_speed_10m"],
    "recorded_at": recorded_at,
    "source": "Open-Meteo",
}