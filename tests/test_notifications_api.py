
import pytest

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.user import User
from app.models.notification import Notification
from app.models.device_token import DeviceToken
from app.models.notification_preference import NotificationPreference


# Creates two real citizen accounts for testing notification ownership.
@pytest.fixture()
def notification_users(app):
    with app.app_context():
        first_user = User(
            name="Notification Citizen One",
            email="notification_citizen1@example.com"
        )
        first_user.set_password("TestPassword123")

        second_user = User(
            name="Notification Citizen Two",
            email="notification_citizen2@example.com"
        )
        second_user.set_password("TestPassword123")

        db.session.add_all([first_user, second_user])
        db.session.commit()

        user_ids = {
            "first": first_user.id,
            "second": second_user.id
        }

        yield user_ids


# Creates an API test client authenticated as the specified citizen.
@pytest.fixture()
def notification_clients(app, notification_users):
    with app.app_context():
        clients = {}

        for name, user_id in notification_users.items():
            access_token = create_access_token(
                identity=str(user_id)
            )

            test_client = app.test_client()
            test_client.environ_base["HTTP_AUTHORIZATION"] = (
                f"Bearer {access_token}"
            )

            clients[name] = test_client

        yield clients


#
# Tests that an authenticated citizen can register an Android device.
def test_register_android_device(
    app,
    notification_users,
    notification_clients
):
    response = notification_clients["first"].post(
        "/api/notifications/device-token",
        json={
            "fid": "test-android-firebase-installation-id",
            "platform": "android"
        }
    )

    assert response.status_code == 201

    response_data = response.get_json()

    assert response_data["status"] == "success"
    assert response_data["device"]["fid"] == (
        "test-android-firebase-installation-id"
    )
    assert response_data["device"]["platform"] == "android"
    assert response_data["device"]["is_active"] is True

    with app.app_context():
        device = DeviceToken.query.filter_by(
            fid="test-android-firebase-installation-id"
        ).first()

        assert device is not None
        assert device.user_id == notification_users["first"]


# Tests that invalid device registration data is rejected.
@pytest.mark.parametrize(
    "payload",
    [
        {"platform": "android"},
        {"token": "test-token"},
        {"token": "", "platform": "android"},
        {"token": "test-token", "platform": "windows"}
    ]
)
def test_register_device_rejects_invalid_data(
    notification_clients,
    payload
):
    response = notification_clients["first"].post(
        "/api/notifications/device-token",
        json=payload
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


# Tests that a citizen can retrieve their own notification history.
def test_get_notification_history(
    app,
    notification_users,
    notification_clients
):
    with app.app_context():
        notification = Notification(
            user_id=notification_users["first"],
            title="Flood Alert",
            message="High flood risk detected in your area.",
            notification_type="flood_alert",
            risk_level="high",
            delivery_status="sent"
        )

        db.session.add(notification)
        db.session.commit()

    response = notification_clients["first"].get(
        "/api/notifications"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["pagination"]["total"] == 1
    assert data["notifications"][0]["title"] == "Flood Alert"
    assert data["notifications"][0]["risk_level"] == "high"


# Tests that a citizen cannot see another citizen's notifications.
def test_notification_history_is_user_specific(
    app,
    notification_users,
    notification_clients
):
    with app.app_context():
        notification = Notification(
            user_id=notification_users["first"],
            title="Private Citizen Alert",
            message="This belongs to the first citizen.",
            notification_type="flood_alert",
            delivery_status="sent"
        )

        db.session.add(notification)
        db.session.commit()

    response = notification_clients["second"].get(
        "/api/notifications"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["pagination"]["total"] == 0
    assert data["notifications"] == []


# Tests notification history pagination and read-status filtering.
def test_notification_pagination_and_read_filter(
    app,
    notification_users,
    notification_clients
):
    with app.app_context():
        user_id = notification_users["first"]

        notifications = [
            Notification(
                user_id=user_id,
                title=f"Flood Alert {number}",
                message="Test notification.",
                notification_type="flood_alert",
                is_read=(number == 1),
                delivery_status="sent"
            )
            for number in range(1, 4)
        ]

        db.session.add_all(notifications)
        db.session.commit()

    response = notification_clients["first"].get(
        "/api/notifications?page=1&per_page=2&is_read=false"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["pagination"]["total"] == 2
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 2

    assert all(
        notification["is_read"] is False
        for notification in data["notifications"]
    )


# Tests that invalid pagination and read-status parameters are rejected.
@pytest.mark.parametrize(
    "query_string",
    [
        "page=0",
        "per_page=0",
        "per_page=101",
        "is_read=maybe"
    ]
)
def test_notification_history_rejects_invalid_filters(
    notification_clients,
    query_string
):
    response = notification_clients["first"].get(
        f"/api/notifications?{query_string}"
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


# Tests that a citizen can mark their own notification as read.
def test_mark_notification_as_read(
    app,
    notification_users,
    notification_clients
):
    with app.app_context():
        notification = Notification(
            user_id=notification_users["first"],
            title="Flood Alert",
            message="Waterlogging detected.",
            notification_type="flood_alert",
            is_read=False,
            delivery_status="sent"
        )

        db.session.add(notification)
        db.session.commit()

        notification_id = notification.id

    response = notification_clients["first"].patch(
        f"/api/notifications/{notification_id}/read"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["notification"]["is_read"] is True
    assert data["notification"]["read_at"] is not None

    with app.app_context():
        saved_notification = db.session.get(
            Notification,
            notification_id
        )

        assert saved_notification.is_read is True
        assert saved_notification.read_at is not None


# Tests that a citizen cannot mark another citizen's notification as read.
def test_citizen_cannot_mark_another_users_notification_as_read(
    app,
    notification_users,
    notification_clients
):
    with app.app_context():
        notification = Notification(
            user_id=notification_users["first"],
            title="Private Flood Alert",
            message="First citizen's notification.",
            notification_type="flood_alert",
            is_read=False,
            delivery_status="sent"
        )

        db.session.add(notification)
        db.session.commit()

        notification_id = notification.id

    response = notification_clients["second"].patch(
        f"/api/notifications/{notification_id}/read"
    )

    assert response.status_code == 404

    with app.app_context():
        saved_notification = db.session.get(
            Notification,
            notification_id
        )

        assert saved_notification.is_read is False


# Tests that marking a nonexistent notification returns 404.
def test_mark_nonexistent_notification_as_read(
    notification_clients
):
    response = notification_clients["first"].patch(
        "/api/notifications/999999/read"
    )

    assert response.status_code == 404


# Tests that default notification preferences are created for a citizen.
def test_get_default_notification_preferences(
    app,
    notification_users,
    notification_clients
):
    response = notification_clients["first"].get(
        "/api/notifications/preferences"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["preferences"] == {
        "push_enabled": True,
        "high_risk_enabled": True,
        "severe_risk_enabled": True
    }

    with app.app_context():
        preferences = NotificationPreference.query.filter_by(
            user_id=notification_users["first"]
        ).first()

        assert preferences is not None


# Tests that a citizen can update their notification preferences.
def test_update_notification_preferences(
    app,
    notification_users,
    notification_clients
):
    response = notification_clients["first"].patch(
        "/api/notifications/preferences",
        json={
            "high_risk_enabled": False,
            "push_enabled": True
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "success"
    assert data["preferences"]["high_risk_enabled"] is False
    assert data["preferences"]["push_enabled"] is True
    assert data["preferences"]["severe_risk_enabled"] is True

    with app.app_context():
        preferences = NotificationPreference.query.filter_by(
            user_id=notification_users["first"]
        ).first()

        assert preferences.high_risk_enabled is False


# Tests that invalid notification preference values are rejected.
@pytest.mark.parametrize(
    "payload",
    [
        {"push_enabled": "false"},
        {"high_risk_enabled": 1},
        {"unknown_preference": True},
        {}
    ]
)
def test_update_notification_preferences_rejects_invalid_data(
    notification_clients,
    payload
):
    response = notification_clients["first"].patch(
        "/api/notifications/preferences",
        json=payload
    )

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


# Tests that notification endpoints require JWT authentication.
def test_notification_history_requires_authentication(client):
    response = client.get("/api/notifications")

    assert response.status_code == 401
