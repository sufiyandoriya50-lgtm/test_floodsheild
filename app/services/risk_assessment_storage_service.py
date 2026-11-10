
from datetime import datetime, timezone

from app.extensions import db
from app.models.risk_assessment import RiskAssessment


"""
    Saves a combined FloodShield risk assessment to the database.

    The assessment_result must be the dictionary returned
    by assess_flood_risk().
    """
def save_risk_assessment(latitude, longitude, assessment_result):

    if not isinstance(assessment_result, dict):
        raise ValueError("Assessment result must be a dictionary")

    risk_level = assessment_result.get("risk_level")
    risk_score = assessment_result.get("score")

    allowed_levels = {
        "low",
        "moderate",
        "high",
        "severe",
        "insufficient_data",
    }

    if risk_level not in allowed_levels:
        raise ValueError("Invalid risk level")

    if risk_score is not None:
        if (
            isinstance(risk_score, bool)
            or not isinstance(risk_score, (int, float))
            or not 0 <= risk_score <= 100
        ):
            raise ValueError("Risk score must be between 0 and 100")

    completeness = assessment_result.get("completeness_percent", 0)

    if (
        isinstance(completeness, bool)
        or not isinstance(completeness, (int, float))
        or not 0 <= completeness <= 100
    ):
        raise ValueError("Data completeness must be between 0 and 100")

    factor_details = {
        "factors": assessment_result.get("factors", {}),
        "historical_weather_context": assessment_result.get(
            "historical_weather_context"
        ),
    }

    assessment = RiskAssessment(
        latitude=latitude,
        longitude=longitude,
        risk_level=risk_level,
        risk_score=risk_score,
        factor_details=factor_details,
        data_completeness=completeness,
        description=assessment_result.get("message"),
    )

    try:
        db.session.add(assessment)
        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return assessment
