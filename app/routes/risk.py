import math
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.models.weather_record import WeatherRecord
from app.models.historical_weather_record import HistoricalWeatherRecord
from app.models.historical_flood_event import HistoricalFloodEvent
from app.models.flood_report import FloodReport

from app.risk.combined_risk_engine import assess_flood_risk
from app.services.risk_alert_service import send_nearby_risk_alerts

from app.services.risk_assessment_storage_service import (
    save_risk_assessment,
)

from app.services.risk_assessment_query_service import (
    get_risk_assessment,
    get_latest_risk_assessment,
    get_risk_assessment_history,
)

from app.utils.geo import calculate_distance_km


risk_bp = Blueprint("risk", __name__)


# Converts a saved risk assessment database object into API JSON data.
def serialize_assessment(assessment):
    return {
        "id": assessment.id,
        "latitude": assessment.latitude,
        "longitude": assessment.longitude,
        "risk_level": assessment.risk_level,
        "risk_score": assessment.risk_score,
        "data_completeness": assessment.data_completeness,
        "factor_details": assessment.factor_details,
        "description": assessment.description,
        "assessed_at": assessment.assessed_at.isoformat(),
    }


# Validates and reads the location and radius query parameters.
def get_location_parameters():
    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)
    radius_km = request.args.get("radius_km", default=5.0, type=float)

    if latitude is None or longitude is None:
        raise ValueError("latitude and longitude are required")

    values = (latitude, longitude, radius_km)

    import math

    if not all(math.isfinite(value) for value in values):
        raise ValueError("Coordinates and radius must be finite numbers")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    if radius_km <= 0:
        raise ValueError("radius_km must be greater than zero")

    return latitude, longitude, radius_km


# POST /api/risk/assess
# Calculates flood risk for a location and saves the assessment.
@risk_bp.route("/api/risk/assess", methods=["POST"])
@jwt_required()
def create_risk_assessment():
    try:
        latitude, longitude, radius_km = get_location_parameters()

        # Retrieve current weather observations near the requested location.
        weather_candidates = WeatherRecord.query.all()

        weather_records = [
            record
            for record in weather_candidates
            if calculate_distance_km(
                latitude,
                longitude,
                record.latitude,
                record.longitude,
            ) <= radius_km
        ]

        # Retrieve historical flood events.
        historical_events = HistoricalFloodEvent.query.all()

        # Only verified community reports contribute to risk analysis.
        community_reports = FloodReport.query.filter_by(
            status="verified"
        ).all()

        # Retrieve historical weather observations.
        historical_weather_records = HistoricalWeatherRecord.query.all()

        # Run the combined FloodShield risk engine.
        assessment_result = assess_flood_risk(
            latitude=latitude,
            longitude=longitude,
            weather_records=weather_records,
            historical_events=historical_events,
            community_reports=community_reports,
            radius_km=radius_km,
            historical_weather_records=historical_weather_records,
        )

        # Persist the calculated assessment.
        assessment = save_risk_assessment(
            latitude=latitude,
            longitude=longitude,
            assessment_result=assessment_result,
        )
        # Trigger automatic alerts after successfully saving the assessment.
        alert_result = send_nearby_risk_alerts(
            latitude=latitude,
            longitude=longitude,
            risk_level=assessment.risk_level,
            radius_km=3,
        )

        return jsonify({
            "status": "success",
            "message": "Flood risk assessment completed",
            "assessment": serialize_assessment(assessment),
            "alerts": alert_result,
        }), 201

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 400


# GET /api/risk/latest
# Retrieves the latest saved risk assessment near the requested location.
@risk_bp.route("/api/risk/latest", methods=["GET"])
@jwt_required()
def latest_risk_assessment():
    try:
        latitude, longitude, radius_km = get_location_parameters()

        result = get_latest_risk_assessment(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
        )

        if result is None:
            return jsonify({
                "status": "success",
                "message": "No risk assessment found nearby",
                "assessment": None,
            }), 200

        assessment = result["assessment"]

        return jsonify({
            "status": "success",
            "assessment": serialize_assessment(assessment),
            "distance_km": result["distance_km"],
        }), 200

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 400


# GET /api/risk/history
# Retrieves paginated risk assessment history near the requested location.
@risk_bp.route("/api/risk/history", methods=["GET"])
@jwt_required()
def risk_assessment_history():
    try:
        latitude, longitude, radius_km = get_location_parameters()

        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=20, type=int)

        result = get_risk_assessment_history(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            page=page,
            per_page=per_page,
        )

        return jsonify({
            "status": "success",
            "items": [
                {
                    **serialize_assessment(item["assessment"]),
                    "distance_km": item["distance_km"],
                }
                for item in result["items"]
            ],
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "per_page": result["per_page"],
                "pages": result["pages"],
            },
        }), 200

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 400


# GET /api/risk/<assessment_id>
# Retrieves one saved risk assessment using its database ID.
@risk_bp.route("/api/risk/<int:assessment_id>", methods=["GET"])
@jwt_required()
def risk_assessment_details(assessment_id):
    assessment = get_risk_assessment(assessment_id)

    if assessment is None:
        return jsonify({
            "status": "error",
            "message": "Risk assessment not found",
        }), 404

    return jsonify({
        "status": "success",
        "assessment": serialize_assessment(assessment),
    }), 200
