
from flask import Blueprint, jsonify, request

from app.services.historical_weather_query_service import (
    get_historical_weather_record,
    get_historical_weather_records,
)

historical_weather_bp = Blueprint(
    "historical_weather",
    __name__,
)


# GET /api/historical-weather
# Retrieves historical weather observations with optional date,
# location-radius and pagination filters.
@historical_weather_bp.route(
    "/api/historical-weather",
    methods=["GET"],
)
def get_historical_weather():
    try:
        # Read optional filters from URL query parameters.
        latitude = request.args.get("latitude", type=float)
        longitude = request.args.get("longitude", type=float)
        radius_km = request.args.get("radius_km", type=float)

        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=20, type=int)

        # Retrieve matching historical weather observations.
        result = get_historical_weather_records(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            start_date=start_date,
            end_date=end_date,
            page=page,
            per_page=per_page,
        )

        # Location-filtered results use a dictionary.
        if isinstance(result, dict):
            records = result["items"]
            total = result["total"]
            current_page = result["page"]
            page_size = result["per_page"]
            total_pages = result["pages"]

        # Date-only or unfiltered results use Flask-SQLAlchemy pagination.
        else:
            records = result.items
            total = result.total
            current_page = result.page
            page_size = result.per_page
            total_pages = result.pages

        return jsonify({
            "status": "success",
            "message": "Historical weather records retrieved successfully",
            "pagination": {
                "total_records": total,
                "page": current_page,
                "per_page": page_size,
                "total_pages": total_pages,
            },
            "data": [
                {
                    "id": record.id,
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                    "temperature_c": record.temperature_c,
                    "rainfall_mm": record.rainfall_mm,
                    "wind_speed_kmh": record.wind_speed_kmh,
                    "weather_code": record.weather_code,
                    "recorded_at": record.recorded_at.isoformat(),
                    "source": record.source,
                }
                for record in records
            ],
        }), 200

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 400


# GET /api/historical-weather/<record_id>
# Retrieves the details of one historical weather observation.
@historical_weather_bp.route(
    "/api/historical-weather/<int:record_id>",
    methods=["GET"],
)
def get_historical_weather_details(record_id):
    record = get_historical_weather_record(record_id)

    if record is None:
        return jsonify({
            "status": "error",
            "message": "Historical weather record not found",
        }), 404

    return jsonify({
        "status": "success",
        "data": {
            "id": record.id,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "temperature_c": record.temperature_c,
            "rainfall_mm": record.rainfall_mm,
            "wind_speed_kmh": record.wind_speed_kmh,
            "weather_code": record.weather_code,
            "recorded_at": record.recorded_at.isoformat(),
            "source": record.source,
        },
    }), 200
