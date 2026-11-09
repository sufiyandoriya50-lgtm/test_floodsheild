from flask import Blueprint, jsonify, request
from datetime import datetime

from app.services.weather_service import get_current_weather
from app.services.weather_storage_service import save_weather_record
from app.services.weather_query_service import get_latest_weather
from app.services.weather_query_service import get_weather_history
from app.services.weather_query_service import get_weather_history_by_date
weather_bp = Blueprint("weather", __name__)

#gets current weather data from open_meteo api directly
@weather_bp.route("/api/weather/current", methods=["GET"])
def current_weather():
    """
    Get current weather for a geographical location.
    """

    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)

    if latitude is None or longitude is None:
        return (
            jsonify(
                {"status": "error", "message": "Latitude and longitude are required"}
            ),
            400,
        )

    try:
        #fetches live weather data
        weather = get_current_weather(latitude, longitude)
      
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Weather fetched successfully",
                    "data": weather
                }
            ),
            200,
        )

    except ValueError as error:
        return jsonify({"status": "error", "message": str(error)}), 400

    except RuntimeError as error:
        return jsonify({"status": "error", "message": str(error)}), 502

# this gets live weather records from external source and saves it    
@weather_bp.route("/api/weather/collect", methods=["POST"])
def collect_weather():
    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)

    if latitude is None or longitude is None:
        return jsonify({
            "status": "error",
            "message": "Latitude and longitude are required"
        }), 400

    try:
        weather = get_current_weather(latitude, longitude)

        saved_record = save_weather_record(weather)

        return jsonify({
            "status": "success",
            "message": "Weather fetched and saved successfully",
            "data": {
                **weather,
                "database_record_id": saved_record.id
            }
        }), 201

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except RuntimeError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 502
# Retrives existing latest weather data from database and also requested specific data 
@weather_bp.route("/api/weather/latest", methods=["GET"])
def latest_weather():
    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)

    if latitude is None or longitude is None:
        return jsonify({
            "status": "error",
            "message": "Latitude and longitude are required"
        }), 400

    try:
        weather = get_latest_weather(latitude, longitude)

        if weather is None:
            return jsonify({
                "status": "error",
                "message": "No weather records found for these coordinates"
            }), 404

        return jsonify({
            "status": "success",
            "data": weather
        }), 200

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Unable to retrieve weather records"
        }), 500
# to get the records from database in limit under 100 
@weather_bp.route("/api/weather/history", methods=["GET"])
def weather_history():
    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)
    limit = request.args.get("limit", default=24, type=int)

    if latitude is None or longitude is None:
        return jsonify({
            "status": "error",
            "message": "Latitude and longitude are required"
        }), 400

    if limit < 1 or limit > 100:
        return jsonify({
            "status": "error",
            "message": "Limit must be between 1 and 100"
        }), 400

    try:
        records = get_weather_history(
            latitude,
            longitude,
            limit
        )

        return jsonify({
            "status": "success",
            "count": len(records),
            "data": records
        }), 200

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Unable to retrieve weather history"
        }), 500
#this route gives filtered data from database by dates
@weather_bp.route("/api/weather/history/date-range", methods=["GET"])
def weather_history_date_range():
    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if (
        latitude is None
        or longitude is None
        or not start_date
        or not end_date
    ):
        return jsonify({
            "status": "error",
            "message": "Latitude, longitude, start_date and end_date are required"
        }), 400

    try:
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)

        if start_datetime > end_datetime:
            return jsonify({
                "status": "error",
                "message": "start_date must be before or equal to end_date"
            }), 400

        records = get_weather_history_by_date(
            latitude,
            longitude,
            start_date,
            end_date
        )

        return jsonify({
            "status": "success",
            "count": len(records),
            "data": records
        }), 200

    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Invalid date format. Use ISO 8601 format."
        }), 400

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Unable to retrieve weather history"
        }), 500    