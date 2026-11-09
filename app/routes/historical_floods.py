import os
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename

from app.services.historical_flood_import_service import (
    import_historical_flood_csv,
)
from app.extensions import db
from app.models.user import User

from app.services.historical_flood_storage_service import (
    create_historical_flood_event
)

from app.services.historical_flood_query_service import (
    get_historical_flood_event,
    get_all_historical_flood_events
)

from app.utils.auth import admin_required


historical_floods_bp = Blueprint(
    "historical_floods",
    __name__
)


# GET /api/historical-floods
# Retrieves historical flood events with optional filters and pagination.
@historical_floods_bp.route(
    "/api/historical-floods",
    methods=["GET"]
)
def get_historical_floods():

    try:
        severity = request.args.get("severity")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        latitude = request.args.get("latitude", type=float)
        longitude = request.args.get("longitude", type=float)
        radius_km = request.args.get("radius_km", type=float)

        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=20, type=int)

        if page < 1 or per_page < 1 or per_page > 100:
            return jsonify({
                "status": "error",
                "message": "Invalid pagination values"
            }), 400

        result = get_all_historical_flood_events(
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            page=page,
            per_page=per_page
        )

        if isinstance(result, dict):
            events = result["items"]
            total = result["total"]
            current_page = result["page"]
            pages = result["pages"]
        else:
            events = result.items
            total = result.total
            current_page = result.page
            pages = result.pages

        return jsonify({
            "status": "success",
            "total": total,
            "page": current_page,
            "per_page": per_page,
            "pages": pages,
            "events": [
                {
                    "id": event.id,
                    "event_name": event.event_name,
                    "latitude": event.latitude,
                    "longitude": event.longitude,
                    "event_date": event.event_date.isoformat(),
                    "water_depth_cm": event.water_depth_cm,
                    "severity": event.severity,
                    "description": event.description,
                    "source": event.source,
                    "source_reference": event.source_reference
                }
                for event in events
            ]
        }), 200

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to retrieve historical flood events"
        }), 500


# GET /api/historical-floods/<event_id>
# Retrieves the details of one historical flood event.
@historical_floods_bp.route(
    "/api/historical-floods/<int:event_id>",
    methods=["GET"]
)
def get_historical_flood_details(event_id):

    event = get_historical_flood_event(event_id)

    if event is None:
        return jsonify({
            "status": "error",
            "message": "Historical flood event not found"
        }), 404

    return jsonify({
        "status": "success",
        "event": {
            "id": event.id,
            "event_name": event.event_name,
            "latitude": event.latitude,
            "longitude": event.longitude,
            "event_date": event.event_date.isoformat(),
            "water_depth_cm": event.water_depth_cm,
            "severity": event.severity,
            "description": event.description,
            "source": event.source,
            "source_reference": event.source_reference
        }
    }), 200


# POST /api/historical-floods
# Allows an administrator to add a historical flood event.
@historical_floods_bp.route(
    "/api/historical-floods",
    methods=["POST"]
)
@admin_required
def create_historical_flood():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Request body must contain valid JSON"
        }), 400

    try:
        event = create_historical_flood_event(
            event_name=data.get("event_name"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            event_date=data.get("event_date"),
            water_depth_cm=data.get("water_depth_cm"),
            severity=data.get("severity"),
            description=data.get("description"),
            source=data.get("source"),
            source_reference=data.get("source_reference")
        )

        return jsonify({
            "status": "success",
            "message": "Historical flood event created successfully",
            "event_id": event.id
        }), 201

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to create historical flood event"
        }), 500

# POST /api/admin/historical-floods/import
# Allows an administrator to upload a CSV file containing historical flood events.
@historical_floods_bp.route(
    "/api/admin/historical-floods/import",
    methods=["POST"],
)
@admin_required
def import_historical_floods():
    uploaded_file = request.files.get("file")

    if uploaded_file is None or uploaded_file.filename == "":
        return jsonify({
            "status": "error",
            "message": "Please upload a CSV file using the 'file' field",
        }), 400

    filename = secure_filename(uploaded_file.filename)

    if not filename.lower().endswith(".csv"):
        return jsonify({
            "status": "error",
            "message": "Only CSV files are allowed",
        }), 400

    upload_directory = os.path.join(
        current_app.instance_path,
        "uploads",
        "historical_floods",
    )

    os.makedirs(upload_directory, exist_ok=True)

    file_path = os.path.join(upload_directory, filename)

    try:
        uploaded_file.save(file_path)

        result = import_historical_flood_csv(file_path)

        return jsonify({
            "status": "success",
            "message": "Historical flood CSV import completed",
            "result": result,
        }), 200

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error),
        }), 400

    except Exception:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred during CSV import",
        }), 500

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)    