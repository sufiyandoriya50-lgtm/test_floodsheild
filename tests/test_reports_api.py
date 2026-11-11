from app.extensions import db
from app.models.user import User
import pytest
from app.models.flood_report import FloodReport
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from app.models.moderation_history import ModerationHistory
from app.models.report_media import FloodReportMedia
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

# Tests that malformed coordinates are rejected.
@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("latitude", "not-a-number"),
        ("longitude", "not-a-number"),
        ("latitude", "91"),
        ("longitude", "181"),
        ("latitude", "nan"),
        ("longitude", "inf"),
    ],
)
def test_create_report_with_invalid_coordinates(
    auth_client,
    test_user,
    parameter,
    value
):
    query = {
        "latitude": "23.0225",
        "longitude": "72.5714",
    }
    query[parameter] = value

    response = auth_client.post(
        "/api/reports",
        query_string=query
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


# Tests that invalid water-depth values are rejected.
@pytest.mark.parametrize(
    "water_depth",
    ["invalid", "-1", "nan", "inf"],
)
def test_create_report_with_invalid_water_depth(
    auth_client,
    test_user,
    water_depth
):
    response = auth_client.post(
        "/api/reports",
        query_string={
            "latitude": "23.0225",
            "longitude": "72.5714",
            "water_depth_cm": water_depth,
        }
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


# Tests that descriptions exceeding the API limit are rejected.
def test_create_report_with_oversized_description(
    auth_client,
    test_user
):
    response = auth_client.post(
        "/api/reports",
        query_string={
            "latitude": "23.0225",
            "longitude": "72.5714",
            "description": "A" * 2001,
        }
    )

    assert response.status_code == 400
    assert "2000 characters" in response.get_json()["message"]


# Tests that an empty description is normalized to None.
def test_create_report_with_empty_description(
    auth_client,
    test_user
):
    response = auth_client.post(
        "/api/reports",
        query_string={
            "latitude": "23.0225",
            "longitude": "72.5714",
            "description": "   ",
        }
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["description"] is None


# Tests that the authenticated JWT identity determines report ownership.
def test_create_report_ignores_supplied_user_id(
    auth_client,
    test_user
):
    response = auth_client.post(
        "/api/reports",
        query_string={
            "user_id": "99999",
            "latitude": "23.0225",
            "longitude": "72.5714",
        }
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["user_id"] == test_user

# Tests that malformed numeric query parameters are rejected.
@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("page", "abc"),
        ("per_page", "abc"),
        ("latitude", "abc"),
        ("longitude", "abc"),
        ("radius_km", "abc"),
        ("page", ""),
        ("per_page", ""),
    ],
)
def test_get_reports_rejects_invalid_numeric_parameters(
    auth_client,
    parameter,
    value
):
    response = auth_client.get(
        "/api/reports",
        query_string={parameter: value}
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


# Tests that location filters must be supplied together.
def test_get_reports_rejects_incomplete_location_filters(auth_client):
    response = auth_client.get(
        "/api/reports?latitude=23.0225&longitude=72.5714"
    )

    assert response.status_code == 400


# Tests that non-finite location values are rejected.
@pytest.mark.parametrize(
    "value",
    ["nan", "inf", "-inf"],
)
def test_get_reports_rejects_non_finite_location_values(
    auth_client,
    value
):
    response = auth_client.get(
        "/api/reports",
        query_string={
            "latitude": value,
            "longitude": "72.5714",
            "radius_km": "10"
        }
    )

    assert response.status_code == 400


# Tests that incorrectly formatted dates are rejected.
def test_get_reports_rejects_invalid_date_format(auth_client):
    response = auth_client.get(
        "/api/reports?start_date=11-11-2026"
    )

    assert response.status_code == 400


# Tests that the start date cannot be later than the end date.
def test_get_reports_rejects_reversed_date_range(auth_client):
    response = auth_client.get(
        "/api/reports?start_date=2026-11-12&end_date=2026-11-10"
    )

    assert response.status_code == 400


# Tests that valid optional filters still return a successful response.
def test_get_reports_accepts_valid_filters(auth_client, test_user):
    response = auth_client.get(
        "/api/reports",
        query_string={
            "status": "pending",
            "page": "1",
            "per_page": "20",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31"
        }
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "success"
# Creates a flood report for testing report-viewing permissions.
@pytest.fixture()
def access_test_report(app, test_user):
    with app.app_context():
        report = FloodReport(
            user_id=test_user,
            latitude=23.0225,
            longitude=72.5714,
            water_depth_cm=25,
            description="Permission testing report",
            status="pending"
        )

        db.session.add(report)
        db.session.commit()

        return report.id


# Creates an authenticated client for a second citizen.
@pytest.fixture()
def second_citizen_client(app):
    with app.app_context():
        user = User(
            name="Second Citizen",
            email="second_citizen@example.com"
        )
        user.set_password("TestPassword123")

        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))

    client = app.test_client()
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"

    return client

# Verifies that a report owner can view their pending report.
def test_report_owner_can_view_pending_report(
    auth_client,
    access_test_report
):
    response = auth_client.get(
        f"/api/reports/{access_test_report}"
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "success"


# Verifies that another citizen cannot view a pending report.
def test_other_citizen_cannot_view_pending_report(
    second_citizen_client,
    access_test_report
):
    response = second_citizen_client.get(
        f"/api/reports/{access_test_report}"
    )

    assert response.status_code == 403


# Verifies that another citizen can view a verified report.
def test_other_citizen_can_view_verified_report(
    app,
    second_citizen_client,
    access_test_report
):
    with app.app_context():
        report = db.session.get(
            FloodReport,
            access_test_report
        )
        report.status = "verified"
        db.session.commit()

    response = second_citizen_client.get(
        f"/api/reports/{access_test_report}"
    )

    assert response.status_code == 200


# Verifies that another citizen cannot view a rejected report.
def test_other_citizen_cannot_view_rejected_report(
    app,
    second_citizen_client,
    access_test_report
):
    with app.app_context():
        report = db.session.get(
            FloodReport,
            access_test_report
        )
        report.status = "rejected"
        db.session.commit()

    response = second_citizen_client.get(
        f"/api/reports/{access_test_report}"
    )

    assert response.status_code == 403

# Verifies that citizens cannot see another citizen's pending report in the list.
def test_report_list_hides_other_citizens_pending_reports(
    second_citizen_client,
    access_test_report
):
    response = second_citizen_client.get("/api/reports")

    assert response.status_code == 200

    report_ids = [
        report["report_id"]
        for report in response.get_json()["data"]
    ]

    assert access_test_report not in report_ids


# Verifies that citizens can see another citizen's verified report in the list.
def test_report_list_shows_other_citizens_verified_reports(
    app,
    second_citizen_client,
    access_test_report
):
    with app.app_context():
        report = db.session.get(FloodReport, access_test_report)
        report.status = "verified"
        db.session.commit()

    response = second_citizen_client.get("/api/reports")

    assert response.status_code == 200

    report_ids = [
        report["report_id"]
        for report in response.get_json()["data"]
    ]

    assert access_test_report in report_ids


# Verifies that citizens can see their own rejected reports.
def test_report_list_shows_owner_rejected_reports(
    app,
    auth_client,
    access_test_report
):
    with app.app_context():
        report = db.session.get(FloodReport, access_test_report)
        report.status = "rejected"
        db.session.commit()

    response = auth_client.get("/api/reports")

    assert response.status_code == 200

    report_ids = [
        report["report_id"]
        for report in response.get_json()["data"]
    ]

    assert access_test_report in report_ids 

# Verifies that a citizen can filter their own rejected reports.
def test_owner_can_filter_rejected_reports(
    app, auth_client, access_test_report
):
    with app.app_context():
        report = db.session.get(FloodReport, access_test_report)
        report.status = "rejected"
        db.session.commit()

    response = auth_client.get("/api/reports?status=rejected")

    assert response.status_code == 200
    report_ids = [
        report["report_id"]
        for report in response.get_json()["data"]
    ]
    assert access_test_report in report_ids       

# Tests whether the database rejects flood reports with invalid latitude.
def test_database_rejects_invalid_latitude(app, test_user):
    with app.app_context():
        report = FloodReport(
            user_id=test_user,
            latitude=100,
            longitude=75,
            water_depth_cm=10,
            description="Invalid latitude test",
            status="pending"
        )

        db.session.add(report)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


# Tests whether the database rejects flood reports with invalid longitude.
def test_database_rejects_invalid_longitude(app, test_user):
    with app.app_context():
        report = FloodReport(
            user_id=test_user,
            latitude=20,
            longitude=200,
            water_depth_cm=10,
            description="Invalid longitude test",
            status="pending"
        )

        db.session.add(report)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


# Tests whether the database rejects negative water depth.
def test_database_rejects_negative_water_depth(app, test_user):
    with app.app_context():
        report = FloodReport(
            user_id=test_user,
            latitude=20,
            longitude=75,
            water_depth_cm=-5,
            description="Negative water depth test",
            status="pending"
        )

        db.session.add(report)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


# Tests whether the database rejects unsupported report statuses.
def test_database_rejects_invalid_report_status(app, test_user):
    with app.app_context():
        report = FloodReport(
            user_id=test_user,
            latitude=20,
            longitude=75,
            water_depth_cm=10,
            description="Invalid status test",
            status="unknown"
        )

        db.session.add(report)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

# Tests whether the database rejects reports referencing nonexistent users.
def test_database_rejects_report_with_nonexistent_user(app):
    with app.app_context():
        report = FloodReport(
            user_id=-1,
            latitude=20,
            longitude=75,
            water_depth_cm=10,
            description="Foreign key integrity test",
            status="pending"
        )

        db.session.add(report)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

# Tests whether moderation history prevents accidental report deletion.
def test_database_prevents_deleting_report_with_moderation_history(
    app, test_user
):
    with app.app_context():
        report = FloodReport(
            user_id=test_user,
            latitude=20,
            longitude=75,
            status="verified"
        )

        db.session.add(report)
        db.session.commit()

        history = ModerationHistory(
            report_id=report.id,
            admin_id=test_user,
            previous_status="pending",
            new_status="verified"
        )

        db.session.add(history)
        db.session.commit()

        db.session.delete(report)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


# Tests whether uploaded photo records prevent accidental report deletion.
def test_database_prevents_deleting_report_with_media(
    app, test_user
):
    with app.app_context():
        report = FloodReport(
            user_id=test_user,
            latitude=20,
            longitude=75,
            status="verified"
        )

        db.session.add(report)
        db.session.commit()

        media = FloodReportMedia(
            report_id=report.id,
            file_path="uploads/test-protected-image.jpg",
            original_filename="protected-image.jpg",
            mime_type="image/jpeg",
            file_size_bytes=1024
        )

        db.session.add(media)
        db.session.commit()

        db.session.delete(report)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


# Tests whether the database rejects invalid previous moderation statuses.
def test_database_rejects_invalid_previous_moderation_status(app, test_user):
    with app.app_context():
        report = FloodReport(
            user_id=test_user,
            latitude=20,
            longitude=75,
            status="pending"
        )

        db.session.add(report)
        db.session.commit()

        history = ModerationHistory(
            report_id=report.id,
            admin_id=test_user,
            previous_status="invalid",
            new_status="verified"
        )

        db.session.add(history)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()


# Tests whether the database rejects invalid new moderation statuses.
def test_database_rejects_invalid_new_moderation_status(app, test_user):
    with app.app_context():
        report = FloodReport(
            user_id=test_user,
            latitude=20,
            longitude=75,
            status="pending"
        )

        db.session.add(report)
        db.session.commit()

        history = ModerationHistory(
            report_id=report.id,
            admin_id=test_user,
            previous_status="pending",
            new_status="invalid"
        )

        db.session.add(history)

        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

    