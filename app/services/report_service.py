from app.extensions import db
from app.models.flood_report import FloodReport
from app.models.moderation_history import ModerationHistory
from app.utils.geo import calculate_distance_km
def create_flood_report(
    user_id,
    latitude,
    longitude,
    water_depth_cm=None,
    description=None
):
    # Create a new flood report object
    report = FloodReport(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        water_depth_cm=water_depth_cm,
        description=description,
        status="pending"
    )

    # Save the report to the database
    try:
        db.session.add(report)
        db.session.commit()

        return report

    except Exception:
        db.session.rollback()
        raise
from sqlalchemy import or_
"""to get all available flood reports by status filter and also if specific reports of areaa is needed by km radius and pagination added"""

def get_all_flood_reports(
    status=None,
    latitude=None,
    longitude=None,
    radius_km=None,
    page=1,
    per_page=20,
    created_after=None,
    created_before=None,
    visible_to_user_id=None,
    include_all=False
):
    query = FloodReport.query

    # Restrict citizens to their own reports and publicly visible verified reports.
    if not include_all:
        if visible_to_user_id is None:
            raise ValueError("A user ID is required to retrieve visible reports")
    
        query = query.filter(
            or_(
                FloodReport.user_id == visible_to_user_id,
                FloodReport.status == "verified"
            )
        )    # Filter reports by creation date.
    if created_after is not None:
       query = query.filter(FloodReport.created_at >= created_after)

    if created_before is not None:
       query = query.filter(FloodReport.created_at < created_before)

    # Apply status filter.
    if status:
        query = query.filter_by(status=status)

    # Sort newest reports first, using report ID as a stable tie-breaker.
    query = query.order_by(
        FloodReport.created_at.desc(),
        FloodReport.id.desc()
    )    
    # Check whether location filtering is requested.
    location_filter = (
        latitude is not None
        and longitude is not None
        and radius_km is not None
    )

    if location_filter:
        # Load reports matching the status filter.
        all_reports = query.all()

        # Calculate geographic distance for each report.
        filtered_reports = []

        for report in all_reports:
            distance = calculate_distance_km(
                latitude,
                longitude,
                report.latitude,
                report.longitude
            )

            if distance <= radius_km:
                filtered_reports.append((report, distance))

        total = len(filtered_reports)

        # Apply pagination after geographic filtering.
        start = (page - 1) * per_page
        end = start + per_page
        selected_reports = filtered_reports[start:end]

        report_data = [
            {
                "report_id": report.id,
                "user_id": report.user_id,
                "latitude": report.latitude,
                "longitude": report.longitude,
                "water_depth_cm": report.water_depth_cm,
                "description": report.description,
                "status": report.status,
                "distance_km": round(distance, 3),
                "created_at": report.created_at.isoformat()
            }
            for report, distance in selected_reports
        ]

    else:
        # Count reports before applying pagination.
        total = query.count()

        # Retrieve only the requested database page.
        selected_reports = (
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        report_data = [
            {
                "report_id": report.id,
                "user_id": report.user_id,
                "latitude": report.latitude,
                "longitude": report.longitude,
                "water_depth_cm": report.water_depth_cm,
                "description": report.description,
                "status": report.status,
                "created_at": report.created_at.isoformat()
            }
            for report in selected_reports
        ]

    return {
        "reports": report_data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_reports": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }

#this is used to get specific flood report by id
def get_flood_report_by_id(report_id):


    # Search for a report using its primary key
    report = FloodReport.query.filter_by(id=report_id).first()

    # Return None if the report does not exist
    if report is None:
        return None

    # Convert the database object into a dictionary
    return {
        "report_id": report.id,
        "user_id": report.user_id,
        "latitude": report.latitude,
        "longitude": report.longitude,
        "water_depth_cm": report.water_depth_cm,
        "description": report.description,
        "status": report.status,
        "created_at": report.created_at.isoformat()
    }


"""
Updates a flood report's status and records the administrator's action.
Allowed statuses: pending, verified, rejected.
"""
def update_report_status(report_id, new_status, admin_id):

    allowed_statuses = {"pending", "verified", "rejected"}

    if new_status not in allowed_statuses:
        raise ValueError(
            "Status must be pending, verified or rejected"
        )

    report = db.session.get(FloodReport, report_id)

    if report is None:
        return None

    previous_status = report.status

    # Avoid creating duplicate history when the status is unchanged.
    if previous_status == new_status:
        return report

    try:
        # Update the report's current status.
        report.status = new_status

        # Create a history record for this administrator decision.
        history = ModerationHistory(
            report_id=report.id,
            admin_id=admin_id,
            previous_status=previous_status,
            new_status=new_status
        )

        db.session.add(history)

        # Save both changes together.
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return report