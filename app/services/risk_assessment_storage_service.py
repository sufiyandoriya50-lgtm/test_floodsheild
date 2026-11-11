
import math

from app.extensions import db
from app.models.risk_assessment import RiskAssessment


# Validates and stores combined FloodShield risk assessments.
def save_risk_assessment(latitude, longitude, assessment_result):
    """Validate and safely store a combined flood-risk assessment."""

    # Validate the assessment result.
    if not isinstance(assessment_result, dict):
        raise ValueError("Assessment result must be a dictionary")

    # Validate geographic coordinates.
    for value, field_name in (
        (latitude, "Latitude"),
        (longitude, "Longitude"),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{field_name} must be a finite number")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    # Validate the risk classification.
    risk_level = assessment_result.get("risk_level")

    allowed_levels = {
        "low",
        "moderate",
        "high",
        "severe",
        "insufficient_data",
    }

    if not isinstance(risk_level, str) or risk_level not in allowed_levels:
        raise ValueError("Invalid risk level")

    # Validate the numerical risk score.
    risk_score = assessment_result.get("score")

    if risk_score is not None:
        if (
            isinstance(risk_score, bool)
            or not isinstance(risk_score, (int, float))
            or not math.isfinite(risk_score)
            or not 0 <= risk_score <= 100
        ):
            raise ValueError("Risk score must be between 0 and 100")

    # Validate assessment data completeness.
    completeness = assessment_result.get("completeness_percent", 0)

    if (
        isinstance(completeness, bool)
        or not isinstance(completeness, (int, float))
        or not math.isfinite(completeness)
        or not 0 <= completeness <= 100
    ):
        raise ValueError("Data completeness must be between 0 and 100")

    # Validate the structure of individual risk factors.
    factors = assessment_result.get("factors", {})

    if not isinstance(factors, dict):
        raise ValueError("Risk factors must be a dictionary")

    historical_context = assessment_result.get(
        "historical_weather_context"
    )

    if historical_context is not None and not isinstance(
        historical_context, dict
    ):
        raise ValueError(
            "Historical weather context must be a dictionary or None"
        )

    # Validate the optional assessment description.
    description = assessment_result.get("message")

    if description is not None and not isinstance(description, str):
        raise ValueError("Assessment message must be text")

    factor_details = {
        "factors": factors,
        "historical_weather_context": historical_context,
    }

    assessment = RiskAssessment(
        latitude=latitude,
        longitude=longitude,
        risk_level=risk_level,
        risk_score=risk_score,
        factor_details=factor_details,
        data_completeness=completeness,
        description=description,
    )

    # Save safely and roll back if database operations fail.
    try:
        db.session.add(assessment)
        db.session.commit()

        return assessment

    except Exception:
        db.session.rollback()
        raise
