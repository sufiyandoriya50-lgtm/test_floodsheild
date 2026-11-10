
import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.risk_assessment import RiskAssessment
from app.services.risk_assessment_storage_service import (
    save_risk_assessment,
)


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
