
import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db

# Import models so SQLAlchemy registers their database tables.
from app.models.user import User
from app.models.risk_assessment import RiskAssessment
from app.models.weather_record import WeatherRecord
from app.models.historical_weather_record import HistoricalWeatherRecord
from app.models.historical_flood_event import HistoricalFloodEvent
from app.models.flood_report import FloodReport


# Creates an isolated Flask application and temporary database for each test.
@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# Creates a test citizen and returns an authenticated API client.
@pytest.fixture
def auth_client(app):
    with app.app_context():
        user = User(
            name="Risk Test User",
            email="risk_test@example.com",
        )
        user.set_password("RiskTestPassword123")

        db.session.add(user)
        db.session.commit()

    client = app.test_client()

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": "risk_test@example.com",
            "password": "RiskTestPassword123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.get_json()["access_token"]

    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    return client


# Confirms that an authenticated user can calculate and save a risk assessment.
def test_create_risk_assessment(auth_client):
    response = auth_client.post(
        "/api/risk/assess",
        query_string={
            "latitude": 23.0225,
            "longitude": 72.5714,
            "radius_km": 5,
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["status"] == "success"
    assert data["assessment"]["id"] is not None
    assert data["assessment"]["risk_level"] in {
        "low",
        "moderate",
        "high",
        "severe",
        "insufficient_data",
    }


# Confirms that the saved assessment can be retrieved as the latest nearby result.
def test_get_latest_risk_assessment(auth_client):
    create_response = auth_client.post(
        "/api/risk/assess",
        query_string={
            "latitude": 23.0225,
            "longitude": 72.5714,
        },
    )

    assert create_response.status_code == 201

    response = auth_client.get(
        "/api/risk/latest",
        query_string={
            "latitude": 23.0225,
            "longitude": 72.5714,
        },
    )

    assert response.status_code == 200
    assert response.get_json()["assessment"] is not None


# Confirms that the assessment history endpoint returns saved records.
def test_get_risk_assessment_history(auth_client):
    auth_client.post(
        "/api/risk/assess",
        query_string={
            "latitude": 23.0225,
            "longitude": 72.5714,
        },
    )

    response = auth_client.get(
        "/api/risk/history",
        query_string={
            "latitude": 23.0225,
            "longitude": 72.5714,
            "page": 1,
            "per_page": 20,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["pagination"]["total"] >= 1
    assert len(data["items"]) >= 1


# Confirms that an individual saved assessment can be retrieved by its ID.
def test_get_risk_assessment_details(auth_client):
    create_response = auth_client.post(
        "/api/risk/assess",
        query_string={
            "latitude": 23.0225,
            "longitude": 72.5714,
        },
    )

    assessment_id = create_response.get_json()["assessment"]["id"]

    response = auth_client.get(
        f"/api/risk/{assessment_id}"
    )

    assert response.status_code == 200
    assert response.get_json()["assessment"]["id"] == assessment_id


# Confirms that a nonexistent assessment returns HTTP 404.
def test_get_nonexistent_risk_assessment(auth_client):
    response = auth_client.get("/api/risk/999999")

    assert response.status_code == 404


# Confirms that risk assessment endpoints reject unauthenticated requests.
def test_reject_unauthenticated_risk_request(app):
    client = app.test_client()

    response = client.post(
        "/api/risk/assess",
        query_string={
            "latitude": 23.0225,
            "longitude": 72.5714,
        },
    )

    assert response.status_code == 401


# Confirms that invalid coordinates are rejected by the API.
def test_reject_invalid_risk_coordinates(auth_client):
    response = auth_client.post(
        "/api/risk/assess",
        query_string={
            "latitude": 120,
            "longitude": 72.5714,
        },
    )

    assert response.status_code == 400
