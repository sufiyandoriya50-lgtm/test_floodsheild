
import pytest

from datetime import datetime, timezone, timedelta

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.risk_assessment import RiskAssessment

from app.services.risk_assessment_query_service import (
    get_risk_assessment,
    get_latest_risk_assessment,
    get_risk_assessment_history,
)


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def create_assessment(score, assessed_at, latitude=23.0225, longitude=72.5714):
    assessment = RiskAssessment(
        latitude=latitude,
        longitude=longitude,
        risk_level="high",
        risk_score=score,
        factor_details={},
        data_completeness=100,
        assessed_at=assessed_at,
    )

    db.session.add(assessment)
    db.session.commit()

    return assessment


def test_get_risk_assessment_by_id(app):
    assessment = create_assessment(
        73.25,
        datetime.now(timezone.utc),
    )

    result = get_risk_assessment(assessment.id)

    assert result is not None
    assert result.risk_score == 73.25


def test_get_latest_risk_assessment(app):
    now = datetime.now(timezone.utc)

    create_assessment(50, now - timedelta(hours=2))
    latest = create_assessment(80, now)

    result = get_latest_risk_assessment(
        latitude=23.0225,
        longitude=72.5714,
        radius_km=5,
    )

    assert result is not None
    assert result["assessment"].id == latest.id


def test_ignore_assessments_outside_radius(app):
    create_assessment(
        70,
        datetime.now(timezone.utc),
        latitude=23.2,
        longitude=72.5714,
    )

    result = get_latest_risk_assessment(
        latitude=23.0225,
        longitude=72.5714,
        radius_km=5,
    )

    assert result is None


def test_get_risk_assessment_history(app):
    now = datetime.now(timezone.utc)

    create_assessment(40, now - timedelta(hours=3))
    create_assessment(60, now - timedelta(hours=2))
    create_assessment(80, now - timedelta(hours=1))

    result = get_risk_assessment_history(
        latitude=23.0225,
        longitude=72.5714,
        radius_km=5,
        page=1,
        per_page=2,
    )

    assert result["total"] == 3
    assert len(result["items"]) == 2
    assert result["pages"] == 2


def test_reject_invalid_radius(app):
    with pytest.raises(ValueError):
        get_latest_risk_assessment(
            latitude=23.0225,
            longitude=72.5714,
            radius_km=-5,
        )


def test_reject_invalid_page(app):
    with pytest.raises(ValueError):
        get_risk_assessment_history(
            latitude=23.0225,
            longitude=72.5714,
            page=0,
        )
