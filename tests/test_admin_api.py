"""this tile tests that 
Pending reports and permissions	
Individual report details	
Verify/reject workflow	
Moderation history	
Dashboard statistics	
Admin search and filtering"""
import pytest

from datetime import timedelta
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.user import User
from app.models.flood_report import FloodReport
from app.models.moderation_history import ModerationHistory
from flask_jwt_extended import create_access_token


@pytest.fixture
def admin_app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def admin_client(admin_app):
    return admin_app.test_client()


@pytest.fixture
def admin_test_data(admin_app):
    with admin_app.app_context():

        # Create an administrator account.
        admin = User(
            name="Test Administrator",
            email="admin_api_test@example.com",
            role="admin"
        )
        admin.set_password("AdminPassword123")

        # Create an ordinary citizen account.
        citizen = User(
            name="Test Citizen",
            email="citizen_api_test@example.com",
            role="citizen"
        )
        citizen.set_password("CitizenPassword123")

        db.session.add_all([admin, citizen])
        db.session.commit()

        # Create a pending flood report.
        report = FloodReport(
            user_id=citizen.id,
            latitude=23.0225,
            longitude=72.5714,
            water_depth_cm=25,
            description="Waterlogging near Ahmedabad road",
            status="pending"
        )

        db.session.add(report)
        db.session.commit()

        admin_token = create_access_token(
            identity=str(admin.id)
        )

        citizen_token = create_access_token(
            identity=str(citizen.id)
        )

        return {
            "admin_id": admin.id,
            "citizen_id": citizen.id,
            "report_id": report.id,
            "admin_token": admin_token,
            "citizen_token": citizen_token
        }


def auth_header(token):
    return {
        "Authorization": f"Bearer {token}"
    }

# Tests that an administrator can log in using email and password.
def test_admin_can_login_with_email_and_password(admin_client, admin_test_data):

    response = admin_client.post(
        "/api/auth/admin/login",
        json={
            "email": "admin_api_test@example.com",
            "password": "AdminPassword123"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["token_type"] == "Bearer"
    assert data["user"]["role"] == "admin"
    assert data["access_token"]


# Tests that ordinary citizens cannot use administrator login.
def test_citizen_cannot_use_admin_login(admin_client, admin_test_data):

    response = admin_client.post(
        "/api/auth/admin/login",
        json={
            "email": "citizen_api_test@example.com",
            "password": "CitizenPassword123"
        }
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["status"] == "error"
    assert data["message"] == "Invalid email or password"


# Tests that incorrect administrator credentials are rejected.
def test_admin_login_rejects_invalid_password(admin_client, admin_test_data):

    response = admin_client.post(
        "/api/auth/admin/login",
        json={
            "email": "admin_api_test@example.com",
            "password": "WrongPassword123"
        }
    )

    assert response.status_code == 401

# Verifies that administrator login rejects a request without valid JSON.
def test_admin_login_rejects_invalid_json(admin_client):

    response = admin_client.post(
        "/api/auth/admin/login",
        data="invalid json",
        content_type="application/json"
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["status"] == "error"
    assert data["message"] == "Request body must contain valid JSON"


# Verifies that administrator login rejects missing credentials.
def test_admin_login_rejects_missing_credentials(admin_client):

    response = admin_client.post(
        "/api/auth/admin/login",
        json={}
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["status"] == "error"
    assert data["message"] == "Email and password are required"


# Verifies that administrator login rejects an invalid email field.
def test_admin_login_rejects_invalid_email_type(admin_client):

    response = admin_client.post(
        "/api/auth/admin/login",
        json={
            "email": 12345,
            "password": "AdminPassword123"
        }
    )

    assert response.status_code == 400


# Verifies that administrator login rejects an empty password.
def test_admin_login_rejects_empty_password(admin_client):

    response = admin_client.post(
        "/api/auth/admin/login",
        json={
            "email": "admin_api_test@example.com",
            "password": ""
        }
    )

    assert response.status_code == 400

# Verifies that administrator login rejects invalid JSON.
def test_admin_login_rejects_invalid_json(admin_client):

    response = admin_client.post(
        "/api/auth/admin/login",
        data="invalid json",
        content_type="application/json"
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["status"] == "error"
    assert data["message"] == "Request body must contain valid JSON"


# Verifies that administrator login rejects missing credentials.
def test_admin_login_rejects_missing_credentials(admin_client):

    response = admin_client.post(
        "/api/auth/admin/login",
        json={
            "email": "admin_api_test@example.com"
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["status"] == "error"
    assert data["message"] == "Email and password are required"


# Verifies that administrator login rejects non-string credentials.
def test_admin_login_rejects_non_string_credentials(admin_client):

    response = admin_client.post(
        "/api/auth/admin/login",
        json={
            "email": 12345,
            "password": "AdminPassword123"
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["status"] == "error"
    assert data["message"] == "Email and password are required"

# Tests that administrators can retrieve pending reports.
def test_admin_can_get_pending_reports(
    admin_client, admin_test_data
):
    response = admin_client.get(
        "/api/admin/reports/pending",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 200
    assert response.json["total_reports"] == 1


# Tests that citizens cannot access pending reports.
def test_citizen_cannot_get_pending_reports(
    admin_client, admin_test_data
):
    response = admin_client.get(
        "/api/admin/reports/pending",
        headers=auth_header(admin_test_data["citizen_token"])
    )

    assert response.status_code == 403


# Tests that unauthenticated users cannot access admin endpoints.
def test_unauthenticated_user_cannot_access_admin(
    admin_client
):
    response = admin_client.get(
        "/api/admin/reports/pending"
    )

    assert response.status_code == 401


# Tests that a non-numeric JWT identity cannot access administrator endpoints.
def test_admin_rejects_non_numeric_jwt_identity(
    admin_app,
    admin_client
):
    # Create a validly signed JWT with an invalid user identity.
    with admin_app.app_context():
        invalid_token = create_access_token(
            identity="not-a-numeric-user-id"
        )

    # Attempt to access an administrator-only endpoint.
    response = admin_client.get(
        "/api/admin/reports/pending",
        headers=auth_header(invalid_token)
    )

    # The request must be rejected without causing a server error.
    assert response.status_code == 403

    response_data = response.get_json()

    assert response_data["status"] == "error"
    assert response_data["message"] == (
        "Administrator access required"
    )

# Tests that a JWT belonging to a nonexistent user cannot access admin endpoints.
def test_admin_rejects_nonexistent_user_identity(
    admin_app,
    admin_client
):
    # Create a valid JWT for a user ID that does not exist.
    with admin_app.app_context():
        invalid_token = create_access_token(
            identity="99999"
        )

    # Attempt to access an administrator-only endpoint.
    response = admin_client.get(
        "/api/admin/reports/pending",
        headers=auth_header(invalid_token)
    )

    # The nonexistent account must not receive administrator access.
    assert response.status_code == 403

    response_data = response.get_json()

    assert response_data["status"] == "error"
    assert response_data["message"] == (
        "Administrator access required"
    )


# Tests that expired JWT access tokens cannot access administrator endpoints.
def test_admin_rejects_expired_jwt(
    admin_app,
    admin_client,
    admin_test_data
):
    # Generate an administrator token that is already expired.
    with admin_app.app_context():
        expired_token = create_access_token(
            identity=str(admin_test_data["admin_id"]),
            expires_delta=timedelta(seconds=-1)
        )

    # Attempt to access an administrator-only endpoint.
    response = admin_client.get(
        "/api/admin/reports/pending",
        headers=auth_header(expired_token)
    )

    # Expired tokens must be rejected.
    assert response.status_code == 401


# Tests that an administrator loses access after their role is downgraded.
def test_admin_access_revoked_after_role_downgrade(
    admin_app,
    admin_client,
    admin_test_data
):
    # Change the administrator's database role to citizen.
    with admin_app.app_context():
        admin = db.session.get(
            User,
            admin_test_data["admin_id"]
        )

        admin.role = "citizen"
        db.session.commit()

    # Attempt access using the administrator's previously issued JWT.
    response = admin_client.get(
        "/api/admin/reports/pending",
        headers=auth_header(admin_test_data["admin_token"])
    )

    # The old token must no longer grant administrator access.
    assert response.status_code == 403

# Tests that administrators can inspect an individual report.
def test_admin_can_get_report_details(
    admin_client, admin_test_data
):
    report_id = admin_test_data["report_id"]

    response = admin_client.get(
        f"/api/admin/reports/{report_id}",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 200
    assert response.json["report"]["id"] == report_id
    assert response.json["report"]["reporter"]["name"] == "Test Citizen"


# Tests that requesting a nonexistent report returns 404.
def test_admin_get_nonexistent_report(
    admin_client, admin_test_data
):
    response = admin_client.get(
        "/api/admin/reports/99999",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 404


# Tests that administrators can verify reports and create history.
def test_admin_can_verify_report(
    admin_app, admin_client, admin_test_data
):
    report_id = admin_test_data["report_id"]

    response = admin_client.patch(
        f"/api/admin/reports/{report_id}/verify",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 200
    assert response.json["report_status"] == "verified"

    with admin_app.app_context():
        report = db.session.get(FloodReport, report_id)

        history = ModerationHistory.query.filter_by(
            report_id=report_id
        ).first()

        assert report.status == "verified"
        assert history is not None
        assert history.admin_id == admin_test_data["admin_id"]
        assert history.previous_status == "pending"
        assert history.new_status == "verified"


# Tests that administrators can reject reports.
def test_admin_can_reject_report(
    admin_app, admin_client, admin_test_data
):
    report_id = admin_test_data["report_id"]

    response = admin_client.patch(
        f"/api/admin/reports/{report_id}/reject",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 200
    assert response.json["report_status"] == "rejected"

    with admin_app.app_context():
        report = db.session.get(FloodReport, report_id)
        assert report.status == "rejected"


# Tests that citizens cannot verify reports.
def test_citizen_cannot_verify_report(
    admin_client, admin_test_data
):
    report_id = admin_test_data["report_id"]

    response = admin_client.patch(
        f"/api/admin/reports/{report_id}/verify",
        headers=auth_header(admin_test_data["citizen_token"])
    )

    assert response.status_code == 403


# Tests that administrators can retrieve moderation history.
def test_admin_can_get_moderation_history(
    admin_client, admin_test_data
):
    report_id = admin_test_data["report_id"]

    response = admin_client.patch(
        f"/api/admin/reports/{report_id}/verify",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 200

    response = admin_client.get(
        f"/api/admin/reports/{report_id}/history",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 200
    assert response.json["total_actions"] == 1
    assert response.json["history"][0]["new_status"] == "verified"


# Tests that the dashboard returns correct report statistics.
def test_admin_dashboard_statistics(
    admin_client, admin_test_data
):
    response = admin_client.get(
        "/api/admin/dashboard/stats",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 200

    statistics = response.json["statistics"]

    assert statistics["total_reports"] == 1
    assert statistics["pending_reports"] == 1
    assert statistics["verified_reports"] == 0
    assert statistics["rejected_reports"] == 0


# Tests that administrators can search reports by status and description.
def test_admin_can_search_reports(
    admin_client, admin_test_data
):
    response = admin_client.get(
        "/api/admin/reports?status=pending&search=waterlogging",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 200
    assert response.json["total_reports"] == 1


# Tests that invalid status filters are rejected.
def test_admin_search_rejects_invalid_status(
    admin_client, admin_test_data
):
    response = admin_client.get(
        "/api/admin/reports?status=approved",
        headers=auth_header(admin_test_data["admin_token"])
    )

    assert response.status_code == 400