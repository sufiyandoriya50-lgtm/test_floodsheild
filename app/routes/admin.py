from flask import Blueprint, jsonify, request
from sqlalchemy import func
from datetime import datetime, timezone

from app.models.flood_report import FloodReport
from app.utils.auth import admin_required
from app.utils.geo import calculate_distance_km
from app.extensions import db
from app.services.media_service import get_report_media
from app.services.report_service import update_report_status
from flask_jwt_extended import get_jwt_identity
from app.models.moderation_history import ModerationHistory

admin_bp = Blueprint("admin", __name__)


# Retrieves all paginated flood reports waiting for administrator review.
# GET /api/admin/reports/pending
@admin_bp.route("/api/admin/reports/pending", methods=["GET"])
@admin_required
def get_pending_reports():

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    # Validate pagination parameters.
    if page < 1 or per_page < 1 or per_page > 100:
        return (
            jsonify({"status": "error", "message": "Invalid pagination parameters"}),
            400,
        )

    # Retrieve pending reports, newest reports first.
    pagination = (
        FloodReport.query.filter_by(status="pending")
        .order_by(FloodReport.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    reports = []

    for report in pagination.items:
        reports.append(
            {
                "id": report.id,
                "user_id": report.user_id,
                "latitude": report.latitude,
                "longitude": report.longitude,
                "water_depth_cm": report.water_depth_cm,
                "description": report.description,
                "status": report.status,
                "created_at": (
                    report.created_at.isoformat() if report.created_at else None
                ),
            }
        )

    return (
        jsonify(
            {
                "status": "success",
                "total_reports": pagination.total,
                "current_page": pagination.page,
                "per_page": pagination.per_page,
                "total_pages": pagination.pages,
                "reports": reports,
            }
        ),
        200,
    )


# GET /api/admin/reports/<report_id>
# Retrieves full details of one flood report, including reporter information and attached photos.
@admin_bp.route("/api/admin/reports/<int:report_id>", methods=["GET"])
@admin_required
def get_admin_report_details(report_id):

    # Find the requested flood report in the database.
    report = db.session.get(FloodReport, report_id)

    # Return 404 if the report does not exist.
    if report is None:
        return jsonify({"status": "error", "message": "Flood report not found"}), 404

    # Prepare the report details for the API response.
    report_data = {
        "id": report.id,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "water_depth_cm": report.water_depth_cm,
        "description": report.description,
        "status": report.status,
        "created_at": (report.created_at.isoformat() if report.created_at else None),
        "reporter": {
            "id": report.user.id,
            "name": report.user.name,
            "email": report.user.email,
        },
        "media": get_report_media(report.id),
    }

    return jsonify({"status": "success", "report": report_data}), 200


# PATCH /api/admin/reports/<report_id>/verify
# Allows an administrator to verify a citizen's flood report.
@admin_bp.route("/api/admin/reports/<int:report_id>/verify", methods=["PATCH"])
@admin_required
def verify_flood_report(report_id):

    try:
        admin_id = int(get_jwt_identity())

        report = update_report_status(
            report_id=report_id, new_status="verified", admin_id=admin_id
        )
        if report is None:
            return (
                jsonify({"status": "error", "message": "Flood report not found"}),
                404,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Flood report verified successfully",
                    "report_id": report.id,
                    "report_status": report.status,
                }
            ),
            200,
        )

    except Exception:
        db.session.rollback()
        return (
            jsonify({"status": "error", "message": "Unable to verify flood report"}),
            500,
        )


# PATCH /api/admin/reports/<report_id>/reject
# Allows an administrator to reject an invalid or misleading flood report.
@admin_bp.route("/api/admin/reports/<int:report_id>/reject", methods=["PATCH"])
@admin_required
def reject_flood_report(report_id):

    try:
        admin_id = int(get_jwt_identity())

        report = update_report_status(
            report_id=report_id, new_status="rejected", admin_id=admin_id
        )

        if report is None:
            return (
                jsonify({"status": "error", "message": "Flood report not found"}),
                404,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Flood report rejected successfully",
                    "report_id": report.id,
                    "report_status": report.status,
                }
            ),
            200,
        )

    except Exception:
        db.session.rollback()
        return (
            jsonify({"status": "error", "message": "Unable to reject flood report"}),
            500,
        )
    
# GET /api/admin/reports/<report_id>/history
# Retrieves the complete moderation history of a flood report for administrators.
@admin_bp.route(
    "/api/admin/reports/<int:report_id>/history",
    methods=["GET"]
)
@admin_required
def get_report_moderation_history(report_id):

    # Check whether the requested flood report exists.
    report = db.session.get(FloodReport, report_id)

    if report is None:
        return jsonify({
            "status": "error",
            "message": "Flood report not found"
        }), 404

    # Retrieve all moderation actions for this report.
    history_records = (
        ModerationHistory.query
        .filter_by(report_id=report_id)
        .order_by(ModerationHistory.created_at.desc())
        .all()
    )

    history = []

    for record in history_records:
        history.append({
            "id": record.id,
            "report_id": record.report_id,
            "admin_id": record.admin_id,
            "admin_name": record.admin.name,
            "previous_status": record.previous_status,
            "new_status": record.new_status,
            "created_at": (
                record.created_at.isoformat()
                if record.created_at else None
            )
        })

    return jsonify({
        "status": "success",
        "report_id": report_id,
        "total_actions": len(history),
        "history": history
    }), 200

# GET /api/admin/dashboard/stats
# Retrieves report totals, status breakdown and the five most recent reports for the admin dashboard.
@admin_bp.route("/api/admin/dashboard/stats", methods=["GET"])
@admin_required
def get_admin_dashboard_stats():

    # Count reports grouped by their current status.
    status_results = (
        db.session.query(
            FloodReport.status,
            func.count(FloodReport.id)
        )
        .group_by(FloodReport.status)
        .all()
    )

    # Prepare default counts so missing statuses appear as zero.
    status_counts = {
        "pending": 0,
        "verified": 0,
        "rejected": 0
    }

    for status, count in status_results:
        if status in status_counts:
            status_counts[status] = count

    # Calculate the total number of flood reports.
    total_reports = sum(status_counts.values())

    # Retrieve the five newest flood reports.
    recent_reports = (
        FloodReport.query
        .order_by(FloodReport.created_at.desc())
        .limit(5)
        .all()
    )

    recent_data = []

    for report in recent_reports:
        recent_data.append({
            "id": report.id,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "status": report.status,
            "description": report.description,
            "created_at": (
                report.created_at.isoformat()
                if report.created_at else None
            )
        })

    return jsonify({
        "status": "success",
        "statistics": {
            "total_reports": total_reports,
            "pending_reports": status_counts["pending"],
            "verified_reports": status_counts["verified"],
            "rejected_reports": status_counts["rejected"]
        },
        "recent_reports": recent_data
    }), 200

# GET /api/admin/reports
# Searches and filters flood reports by status, description, location and date, with pagination.
@admin_bp.route("/api/admin/reports", methods=["GET"])
@admin_required
def search_admin_reports():

    # Read filters from URL query parameters.
    status = request.args.get("status", "").strip().lower()
    search = request.args.get("search", "").strip()

    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)
    radius_km = request.args.get("radius_km", type=float)

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    # Validate status.
    allowed_statuses = {"pending", "verified", "rejected"}

    if status and status not in allowed_statuses:
        return jsonify({
            "status": "error",
            "message": "Invalid status filter"
        }), 400

    # Validate pagination.
    if page < 1 or per_page < 1 or per_page > 100:
        return jsonify({
            "status": "error",
            "message": "Invalid pagination parameters"
        }), 400

    # Location filters must be supplied together.
    location_values = [latitude, longitude, radius_km]

    if any(value is not None for value in location_values):
        if any(value is None for value in location_values):
            return jsonify({
                "status": "error",
                "message": "latitude, longitude and radius_km are all required"
            }), 400

        if (
            not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
            or not 0 < radius_km <= 500
        ):
            return jsonify({
                "status": "error",
                "message": "Invalid location or radius values"
            }), 400

    # Parse optional date filters.
    try:
        parsed_start = (
            datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if start_date else None
        )

        parsed_end = (
            datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            if end_date else None
        )

        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise ValueError("Start date must not be after end date")

    except ValueError:
        return jsonify({
            "status": "error",
            "message": "Dates must be valid ISO 8601 date/time values"
        }), 400

    # Start building the database query.
    query = FloodReport.query

    if status:
        query = query.filter_by(status=status)

    if search:
        query = query.filter(
            FloodReport.description.ilike(f"%{search}%")
        )

    # Get matching reports, newest first.
    reports = query.order_by(
        FloodReport.created_at.desc()
    ).all()

    filtered_reports = []

    for report in reports:

        # Apply date filters.
        report_date = report.created_at

        if report_date is not None:
            if report_date.tzinfo is None:
                report_date = report_date.replace(tzinfo=timezone.utc)

            if parsed_start:
                start = parsed_start
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)

                if report_date < start:
                    continue

            if parsed_end:
                end = parsed_end
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)

                if report_date > end:
                    continue

        # Apply distance filter.
        if latitude is not None:
            distance = calculate_distance_km(
                latitude,
                longitude,
                report.latitude,
                report.longitude
            )

            if distance > radius_km:
                continue

        filtered_reports.append(report)

    # Calculate pagination after applying all filters.
    total_reports = len(filtered_reports)
    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    paginated_reports = filtered_reports[start_index:end_index]

    report_data = []

    for report in paginated_reports:
        report_data.append({
            "id": report.id,
            "user_id": report.user_id,
            "latitude": report.latitude,
            "longitude": report.longitude,
            "water_depth_cm": report.water_depth_cm,
            "description": report.description,
            "status": report.status,
            "created_at": (
                report.created_at.isoformat()
                if report.created_at else None
            )
        })

    total_pages = (
        (total_reports + per_page - 1) // per_page
    )

    return jsonify({
        "status": "success",
        "total_reports": total_reports,
        "current_page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "reports": report_data
    }), 200