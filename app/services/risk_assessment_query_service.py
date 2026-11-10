
from datetime import datetime, timezone

from app.extensions import db
from app.models.risk_assessment import RiskAssessment
from app.utils.geo import calculate_distance_km


# Retrieves a single saved risk assessment using its database ID.
def get_risk_assessment(assessment_id):
    if (
        isinstance(assessment_id, bool)
        or not isinstance(assessment_id, int)
        or assessment_id <= 0
    ):
        raise ValueError("Assessment ID must be a positive integer")

    return db.session.get(RiskAssessment, assessment_id)


# Retrieves the latest saved risk assessment for a specific location.
def get_latest_risk_assessment(latitude, longitude, radius_km=5.0):
    validate_location(latitude, longitude, radius_km)

    candidates = (
        RiskAssessment.query
        .order_by(RiskAssessment.assessed_at.desc(), RiskAssessment.id.desc())
        .all()
    )

    nearby_assessments = []

    for assessment in candidates:
        distance = calculate_distance_km(
            latitude,
            longitude,
            assessment.latitude,
            assessment.longitude,
        )

        if distance <= radius_km:
            nearby_assessments.append((assessment, distance))

    if not nearby_assessments:
        return None

    # The database query is newest-first, so the first nearby result is latest.
    assessment, distance = nearby_assessments[0]

    return {
        "assessment": assessment,
        "distance_km": round(distance, 3),
    }


# Retrieves paginated risk assessment history for a geographic area.
def get_risk_assessment_history(
    latitude,
    longitude,
    radius_km=5.0,
    page=1,
    per_page=20,
):
    validate_location(latitude, longitude, radius_km)

    if (
        isinstance(page, bool)
        or not isinstance(page, int)
        or page < 1
    ):
        raise ValueError("Page must be a positive integer")

    if (
        isinstance(per_page, bool)
        or not isinstance(per_page, int)
        or not 1 <= per_page <= 100
    ):
        raise ValueError("Per-page must be between 1 and 100")

    candidates = (
        RiskAssessment.query
        .order_by(RiskAssessment.assessed_at.desc(), RiskAssessment.id.desc())
        .all()
    )

    nearby_assessments = []

    for assessment in candidates:
        distance = calculate_distance_km(
            latitude,
            longitude,
            assessment.latitude,
            assessment.longitude,
        )

        if distance <= radius_km:
            nearby_assessments.append({
                "assessment": assessment,
                "distance_km": round(distance, 3),
            })

    total = len(nearby_assessments)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "items": nearby_assessments[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


# Validates the geographic coordinates and search radius.
def validate_location(latitude, longitude, radius_km):
    values = (latitude, longitude, radius_km)

    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        for value in values
    ):
        raise ValueError("Coordinates and radius must be numeric")

    if not all(
        __import__("math").isfinite(value)
        for value in values
    ):
        raise ValueError("Coordinates and radius must be finite")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    if radius_km <= 0:
        raise ValueError("Radius must be greater than zero")
