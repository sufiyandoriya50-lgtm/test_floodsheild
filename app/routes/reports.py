import math
from app.extensions import db
from datetime import datetime, timedelta, timezone
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.auth import admin_required
from app.extensions import db
from flask import Blueprint, jsonify, request
from flask import send_from_directory, abort, current_app
import os

from app.models.user import User
from app.services.report_service import (
    create_flood_report,
    get_all_flood_reports,
    get_flood_report_by_id
)
from app.models.flood_report import FloodReport
from app.models.report_media import FloodReportMedia
from app.services.media_service import (
    save_report_media,
    get_report_media,
    delete_report_media
)
from app.services.report_service import update_report_status



reports_bp = Blueprint("reports", __name__)


# POST /api/reports
# Creates a flood report for the citizen authenticated through a JWT access token.
@reports_bp.route("/api/reports", methods=["POST"])
@jwt_required()
def submit_report():

    # Step 1: Get the authenticated user's ID from the JWT.
    user_id = int(get_jwt_identity())

    # Read the remaining values from URL query parameters.
    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)
    water_depth_cm = request.args.get("water_depth_cm", type=float)
    description = request.args.get("description")

    # Step 2: Check required values.
    if latitude is None or longitude is None:
        return (
            jsonify({
                "status": "error",
                "message": "Latitude and longitude are required",
            }),
            400,
        )

    # Step 3: Validate the authenticated user ID.
    if user_id <= 0:
        return jsonify({"status": "error", "message": "Invalid user identity"}), 400

    # Step 4: Validate coordinates.
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        return jsonify({"status": "error", "message": "Invalid latitude"}), 400

    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        return jsonify({"status": "error", "message": "Invalid longitude"}), 400

    # Step 5: Validate optional water depth.
    if water_depth_cm is not None:
        if not math.isfinite(water_depth_cm) or water_depth_cm < 0:
            return (
                jsonify({
                    "status": "error",
                    "message": "Water depth must be a non-negative number",
                }),
                400,
            )

    # Step 6: Check whether the authenticated user still exists.
    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Step 7: Create and save the flood report.
    try:
        report = create_flood_report(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude,
            water_depth_cm=water_depth_cm,
            description=description,
        )

        # Step 8: Return the successful response.
        return (
            jsonify({
                "status": "success",
                "message": "Flood report submitted successfully",
                "data": {
                    "report_id": report.id,
                    "user_id": report.user_id,
                    "latitude": report.latitude,
                    "longitude": report.longitude,
                    "water_depth_cm": report.water_depth_cm,
                    "description": report.description,
                    "report_status": report.status,
                },
            }),
            201,
        )

    except Exception:
        db.session.rollback()

        return (
            jsonify({
                "status": "error",
                "message": "Unable to save flood report",
            }),
            500,
        )

# api to get all user given reports using optional location, status, date and pagination filters.
@reports_bp.route("/api/reports", methods=["GET"])
@jwt_required()
def get_reports():
    # gets and checks if status valid or not
    status = request.args.get("status")
    allowed_statuses = {"pending", "verified"}

    if status is not None:
        status = status.strip().lower()

        if status not in allowed_statuses:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Invalid report status",
                        "allowed_statuses": sorted(allowed_statuses),
                    }
                ),
                400,
            )
    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)
    radius_km = request.args.get("radius_km", type=float)
    # gets page args from url
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    
    created_after = None
    created_before = None
    
    try:
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            created_after = datetime.combine(
            start, datetime.min.time(), tzinfo=timezone.utc
            )
    
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            created_before = datetime.combine(
            end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc
            )
    
    except ValueError:
            return (
        jsonify({"status": "error", "message": "Dates must use YYYY-MM-DD format"}),
            400,
        )
    
    if start_date and end_date and start > end:
        return (
        jsonify({"status": "error", "message": "start_date cannot be after end_date"}),
            400,
        )

    # pagination checks
    if page < 1:
        return jsonify({"status": "error", "message": "Page must be at least 1"}), 400

    if per_page < 1 or per_page > 100:
        return (
            jsonify(
                {"status": "error", "message": "per_page must be between 1 and 100"}
            ),
            400,
        )

    # Location filters must be supplied together.
    location_values = (latitude, longitude, radius_km)

    if any(value is not None for value in location_values):
        if any(value is None for value in location_values):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "latitude, longitude and radius_km are all required",
                    }
                ),
                400,
            )

        if not (
            math.isfinite(latitude)
            and math.isfinite(longitude)
            and math.isfinite(radius_km)
        ):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Location values must be finite numbers",
                    }
                ),
                400,
            )

        if not -90 <= latitude <= 90:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Latitude must be between -90 and 90",
                    }
                ),
                400,
            )

        if not -180 <= longitude <= 180:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Longitude must be between -180 and 180",
                    }
                ),
                400,
            )

        if radius_km <= 0 or radius_km > 100:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "radius_km must be greater than 0 and at most 100",
                    }
                ),
                400,
            )

    result = get_all_flood_reports(
        status=status,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        page=page,
        per_page=per_page,
        created_after=created_after,
        created_before=created_before
    )

    return (
        jsonify(
            {
                "status": "success",
                "message": "Flood reports retrieved successfully",
                "count": len(result["reports"]),
                "data": result["reports"],
                "pagination": result["pagination"],
            }
        ),
        200,
    )

# GET /api/reports/<report_id>
# Retrieves one flood report along with all photographs attached to it.
@reports_bp.route(
    "/api/reports/<int:report_id>",
    methods=["GET"]
)
@jwt_required()
def get_report(report_id):

    report = get_flood_report_by_id(report_id)

    if report is None:
        return jsonify({
            "status": "error",
            "message": "Flood report not found"
        }), 404

    media_records = get_report_media(report_id)

    return jsonify({
        "status": "success",
        "message": "Flood report retrieved successfully",
        "data": {
            **report,
            "media": media_records
        }
    }), 200

# api to get number of photos uploaded by user and (sends to media service which validates and saves it to db)also checks if report exist or not 
@reports_bp.route(
    "/api/reports/<int:report_id>/media",
    methods=["POST"]
)
@jwt_required()
def upload_report_media(report_id):

    # Find the report that will receive the photographs.
    report = db.session.get(FloodReport, report_id)
    # Identify the citizen authenticated by the JWT.
    current_user_id = int(get_jwt_identity())

    # Only the report owner can upload photographs.
    if report.user_id != current_user_id:
        return jsonify({
        "status": "error",
        "message": "You are not authorized to upload photos to this report"
        }), 403
    if report is None:
        return jsonify({
            "status": "error",
            "message": "Flood report not found"
        }), 404
    # Identify the citizen authenticated by the JWT.
    current_user_id = int(get_jwt_identity())

    # Only the report owner can upload photographs.
    if report.user_id != current_user_id:
       return jsonify({
        "status": "error",
        "message": "You are not authorized to upload photos to this report"
    }), 403

    # Get all uploaded files with the field name "photos".
    uploaded_files = request.files.getlist("photos")

    if not uploaded_files or any(
        not file.filename for file in uploaded_files
    ):
        return jsonify({
            "status": "error",
            "message": "Please select at least one photograph"
        }), 400

    if len(uploaded_files) > 3:
        return jsonify({
            "status": "error",
            "message": "You can upload a maximum of 3 photographs at once"
        }), 400

    # Enforce a maximum of three photographs per report.
    existing_count = FloodReportMedia.query.filter_by(
        report_id=report_id
    ).count()

    if existing_count + len(uploaded_files) > 3:
        return jsonify({
            "status": "error",
            "message": "A flood report can have a maximum of 3 photographs"
        }), 400

    try:
        media_records = save_report_media(
            report,
            uploaded_files
        )

        return jsonify({
            "status": "success",
            "message": "Photographs uploaded successfully",
            "count": len(media_records),
            "data": [
                {
                    "media_id": media.id,
                    "report_id": media.report_id,
                    "original_filename": media.original_filename,
                    "mime_type": media.mime_type,
                    "file_size_bytes": media.file_size_bytes,
                    "file_path": media.file_path
                }
                for media in media_records
            ]
        }), 201

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Unable to upload photographs"
        }), 500

# the api route to  get request of image send it to media_service then receives data and api send to user from backend according to report
@reports_bp.route(
    "/api/reports/<int:report_id>/media",
    methods=["GET"]
)
@jwt_required()
def list_report_media(report_id):
    report = db.session.get(FloodReport, report_id)

    if report is None:
        return jsonify({
            "status": "error",
            "message": "Flood report not found"
        }), 404

    media_records = get_report_media(report_id)

    return jsonify({
        "status": "success",
        "message": "Report photographs retrieved successfully",
        "count": len(media_records),
        "data": media_records
    }), 200

# GET /api/reports/<report_id>/media/<media_id>
# Retrieves and displays the actual photograph attached to a flood report.
@reports_bp.route(
    "/api/reports/<int:report_id>/media/<int:media_id>",
    methods=["GET"]
)
@jwt_required()
def view_report_media(report_id, media_id):

    media = FloodReportMedia.query.filter_by(
        id=media_id,
        report_id=report_id
    ).first()

    if media is None:
        return jsonify({
            "status": "error",
            "message": "Photograph not found"
        }), 404

    upload_directory = os.path.join(
        current_app.instance_path,
        "uploads",
        "reports"
    )

    filename = os.path.basename(media.file_path)

    return send_from_directory(
        upload_directory,
        filename,
        mimetype=media.mime_type
    )

# DELETE /api/reports/<report_id>/media/<media_id>
# Deletes a specific photograph and its database record from a flood report.
@reports_bp.route(
    "/api/reports/<int:report_id>/media/<int:media_id>",
    methods=["DELETE"]
)
@jwt_required()
def remove_report_media(report_id, media_id):

    try:
        # Step 1: Retrieve the flood report containing the photograph.
        report = db.session.get(FloodReport, report_id)

        # Step 2: Check whether the report exists.
        if report is None:
            return jsonify({
                "status": "error",
                "message": "Flood report not found"
            }), 404

        # Step 3: Identify the authenticated citizen.
        current_user_id = int(get_jwt_identity())

        # Step 4: Only the report owner can delete its photographs.
        if report.user_id != current_user_id:
            return jsonify({
                "status": "error",
                "message": "You are not authorized to delete photos from this report"
            }), 403

        # Step 5: Delete the photograph using the existing service.
        deleted = delete_report_media(report_id, media_id)

        # Step 6: Check whether the photograph was found.
        if not deleted:
            return jsonify({
                "status": "error",
                "message": "Photograph not found"
            }), 404

        # Step 7: Return the successful response.
        return jsonify({
            "status": "success",
            "message": "Photograph deleted successfully",
            "report_id": report_id,
            "media_id": media_id
        }), 200

    except Exception:
        # Log the actual error for backend debugging.
        current_app.logger.exception(
            "Failed to delete photograph %s from report %s",
            media_id,
            report_id
        )

        return jsonify({
            "status": "error",
            "message": "Unable to delete photograph"
        }), 500


# Updates a flood report's review status to pending, verified or rejected.
# PATCH /api/reports/<report_id>/status
@reports_bp.route(
    "/api/reports/<int:report_id>/status",
    methods=["PATCH"]
)
@admin_required
def update_flood_report_status(report_id):

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Request body must contain valid JSON"
        }), 400

    new_status = data.get("status")

    if not isinstance(new_status, str):
        return jsonify({
            "status": "error",
            "message": "Status is required"
        }), 400

    try:
        report = update_report_status(
            report_id=report_id,
            new_status=new_status.strip().lower()
        )

        if report is None:
            return jsonify({
                "status": "error",
                "message": "Flood report not found"
            }), 404

        return jsonify({
            "status": "success",
            "message": "Flood report status updated successfully",
            "report": {
                "id": report.id,
                "status": report.status
            }
        }), 200

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except Exception:
        return jsonify({
            "status": "error",
            "message": "Unable to update flood report status"
        }), 500
