from app.extensions import db
from app.models.user import User
import pytest


# Creates a test citizen in the isolated test database.
@pytest.fixture()
def test_user(app):
    with app.app_context():
        user = User(
            name="FloodShield Test User",
            email="test@example.com"
        )
        user.set_password("TestPassword123")

        db.session.add(user)
        db.session.commit()

        return user.id


# Tests whether a citizen can submit a valid flood report.
def test_create_flood_report(auth_client, test_user):
    response = auth_client.post(
        f"/api/reports?user_id={test_user}"
        "&latitude=23.0225"
        "&longitude=72.5714"
        "&water_depth_cm=25"
        "&description=Waterlogging near test road"
    )

    assert response.status_code == 201

    response_data = response.get_json()

    assert response_data["status"] == "success"
    assert response_data["data"]["latitude"] == 23.0225
    assert response_data["data"]["longitude"] == 72.5714
    assert response_data["data"]["water_depth_cm"] == 25.0


# Tests whether the API rejects a report with an invalid user ID.
def test_create_report_with_missing_user(auth_client):
    response = auth_client.post(
        "/api/reports?user_id=99999"
        "&latitude=23.0225"
        "&longitude=72.5714"
    )

    assert response.status_code == 404