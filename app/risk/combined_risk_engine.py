
from datetime import datetime, timezone

from app.risk.rainfall_analyzer import analyze_rainfall
from app.risk.historical_flood_analyzer import (
    analyze_historical_flood_risk,
)
from app.risk.historical_weather_analyzer import analyze_historical_weather
from app.risk.community_report_analyzer import (
    analyze_community_reports,
)


# Provisional weights for the three risk factors.
RISK_WEIGHTS = {
    "rainfall": 40,
    "community_reports": 35,
    "historical_floods": 25,
}


"""
    Converts a numerical risk score into a risk category.
    These thresholds are provisional, not validated flood probabilities.
    """
def classify_risk(score):
    if score < 25:
        return "low"

    if score < 50:
        return "moderate"

    if score < 75:
        return "high"

    return "severe"


"""
    Combines only available risk factors.

    Missing factors are excluded and the remaining weights
    are proportionally normalized.
    """
def calculate_weighted_risk(factors):
    available_factors = {}

    for name, result in factors.items():
        if result.get("available") is True:
            score = result.get("score")

            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not 0 <= score <= 100
            ):
                raise ValueError(
                    f"Invalid risk score for {name}"
                )

            available_factors[name] = score

    if not available_factors:
        return None

    available_weight = sum(
        RISK_WEIGHTS[name]
        for name in available_factors
    )

    weighted_total = sum(
        available_factors[name] * RISK_WEIGHTS[name]
        for name in available_factors
    )

    return round(weighted_total / available_weight, 2)


""" 
    Calculates a combined FloodShield flood-risk assessment.

    It combines rainfall, historical flood events and verified
    community reports without depending on an AI model.
    """
def assess_flood_risk(
    latitude,
    longitude,
    weather_records,
    historical_events,
    community_reports,
    radius_km=5.0,
    now=None,
    historical_weather_records=None
):
    if now is None:
        now = datetime.now(timezone.utc)

    # Analyze the three independent risk signals.
    rainfall_result = analyze_rainfall(
        weather_records,
        now=now,
    )

    historical_result = analyze_historical_flood_risk(
        historical_events,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )

    community_result = analyze_community_reports(
        community_reports,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        now=now,
    )
    if historical_weather_records is None:
        historical_weather_records = []

    historical_weather_result = analyze_historical_weather(
        records=historical_weather_records,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        now=now
    )
    factors = {
        "rainfall": rainfall_result,
        "historical_floods": historical_result,
        "community_reports": community_result,
    }

    # Combine available factors, excluding missing data.
    combined_score = calculate_weighted_risk(factors)

    if combined_score is None:
        return {
            "available": False,
            "risk_level": "insufficient_data",
            "risk_score": None,
            "data_completeness_percent": 0,
            "factors": factors,
            "message": (
                "Insufficient data to calculate flood risk."
            ),
            "assessed_at": now.isoformat(),
        }

    available_weight = sum(
        RISK_WEIGHTS[name]
        for name, result in factors.items()
        if result.get("available") is True
    )

    return {
        "available": True,
        "risk_level": classify_risk(combined_score),
        "risk_score": combined_score,
        "data_completeness_percent": available_weight,
        "factors": factors,
        "message": (
            "Flood risk calculated using available "
            "weather, historical and community data."
        ),
        "assessed_at": now.isoformat(),
        "historical_weather_context": historical_weather_result,
    }
