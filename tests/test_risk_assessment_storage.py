
import pytest
from datetime import timezone,datetime
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.risk_assessment import RiskAssessment
from app.services.risk_assessment_storage_service import (
    save_risk_assessment,
)
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_save_risk_assessment(app):
    result = {
        "risk_level": "high",
        "score": 73.25,
        "completeness_percent": 100,
        "factors": {
            "rainfall": {"available": True, "score": 80},
            "historical_floods": {"available": True, "score": 60},
            "community_reports": {"available": True, "score": 75},
        },
        "historical_weather_context": {
            "available": True,
            "category": "severe",
        },
        "message": "High flood risk detected",
    }

    assessment = save_risk_assessment(
        latitude=23.0225,
        longitude=72.5714,
        assessment_result=result,
    )

    saved = db.session.get(RiskAssessment, assessment.id)

    assert saved is not None
    assert saved.risk_level == "high"
    assert saved.risk_score == 73.25
    assert saved.data_completeness == 100
    assert saved.factor_details["factors"]["rainfall"]["score"] == 80
    assert (
        saved.factor_details["historical_weather_context"]["category"]
        == "severe"
    )


def test_save_insufficient_data_assessment(app):
    result = {
        "risk_level": "insufficient_data",
        "score": None,
        "completeness_percent": 0,
        "factors": {},
        "historical_weather_context": {"available": False},
        "message": "Insufficient data for risk assessment",
    }

    assessment = save_risk_assessment(
        latitude=23.0225,
        longitude=72.5714,
        assessment_result=result,
    )

    assert assessment.risk_level == "insufficient_data"
    assert assessment.risk_score is None


def test_reject_invalid_risk_level(app):
    result = {
        "risk_level": "unknown",
        "score": 50,
        "completeness_percent": 100,
    }

    with pytest.raises(ValueError):
        save_risk_assessment(
            latitude=23.0225,
            longitude=72.5714,
            assessment_result=result,
        )


def test_reject_invalid_risk_score(app):
    result = {
        "risk_level": "high",
        "score": 150,
        "completeness_percent": 100,
    }

    with pytest.raises(ValueError):
        save_risk_assessment(
            latitude=23.0225,
            longitude=72.5714,
            assessment_result=result,
        )

# Verifies that invalid geographic coordinates are rejected.
@pytest.mark.parametrize(
    "latitude, longitude",
    [
        (91, 72.5714),
        (-91, 72.5714),
        (23.0225, 181),
        (23.0225, -181),
        (float("nan"), 72.5714),
        (23.0225, float("inf")),
        (True, 72.5714),
    ],
)
def test_reject_invalid_risk_assessment_coordinates(
    app, latitude, longitude
):
    result = {
        "risk_level": "high",
        "score": 70,
        "completeness_percent": 100,
    }

    with pytest.raises(ValueError):
        save_risk_assessment(
            latitude=latitude,
            longitude=longitude,
            assessment_result=result,
        )


# Verifies that invalid risk scores and completeness values are rejected.
@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("score", -1),
        ("score", 101),
        ("score", float("nan")),
        ("score", float("inf")),
        ("score", True),
        ("completeness_percent", -1),
        ("completeness_percent", 101),
        ("completeness_percent", float("nan")),
        ("completeness_percent", float("inf")),
        ("completeness_percent", True),
    ],
)
def test_reject_invalid_risk_assessment_percentages(
    app, field, invalid_value
):
    result = {
        "risk_level": "high",
        "score": 70,
        "completeness_percent": 100,
    }
    result[field] = invalid_value

    with pytest.raises(ValueError):
        save_risk_assessment(
            latitude=23.0225,
            longitude=72.5714,
            assessment_result=result,
        )


# Verifies that invalid risk-factor structures are rejected.
@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("factors", []),
        ("factors", "invalid"),
        ("historical_weather_context", []),
        ("historical_weather_context", "invalid"),
        ("message", 123),
    ],
)
def test_reject_invalid_risk_assessment_details(
    app, field, invalid_value
):
    result = {
        "risk_level": "high",
        "score": 70,
        "completeness_percent": 100,
        "factors": {},
        "historical_weather_context": {},
        "message": "High flood risk",
    }
    result[field] = invalid_value

    with pytest.raises(ValueError):
        save_risk_assessment(
            latitude=23.0225,
            longitude=72.5714,
            assessment_result=result,
        )

# Verifies that database constraints reject invalid risk assessments.
@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("latitude", 91),
        ("longitude", 181),
        ("risk_level", "unknown"),
        ("risk_score", -1),
        ("risk_score", 101),
        ("data_completeness", -1),
        ("data_completeness", 101),
    ],
)
def test_risk_assessment_database_rejects_invalid_data(
    app, field, invalid_value
):
    with app.app_context():
        values = {
            "latitude": 23.0225,
            "longitude": 72.5714,
            "risk_level": "high",
            "risk_score": 70,
            "factor_details": "{}",
            "data_completeness": 100,
            "description": "Database integrity test",
            "assessed_at": datetime.now(timezone.utc).isoformat(),
        }

        values[field] = invalid_value

        with pytest.raises(IntegrityError):
            db.session.execute(
                text("""
                    INSERT INTO risk_assessments (
                        latitude,
                        longitude,
                        risk_level,
                        risk_score,
                        factor_details,
                        data_completeness,
                        description,
                        assessed_at
                    )
                    VALUES (
                        :latitude,
                        :longitude,
                        :risk_level,
                        :risk_score,
                        :factor_details,
                        :data_completeness,
                        :description,
                        :assessed_at
                    )
                """),
                values
            )

        db.session.rollback()


# Verifies that NULL risk scores remain valid for insufficient data.
def test_risk_assessment_database_allows_null_score(app):
    with app.app_context():
        assessment = RiskAssessment(
            latitude=23.0225,
            longitude=72.5714,
            risk_level="insufficient_data",
            risk_score=None,
            factor_details={},
            data_completeness=0,
            description="Insufficient weather and flood data",
        )

        db.session.add(assessment)
        db.session.commit()

        assert assessment.id is not None
        assert assessment.risk_score is None
