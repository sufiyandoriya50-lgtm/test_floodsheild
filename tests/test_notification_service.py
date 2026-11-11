
import pytest
from firebase_admin import messaging

from app.extensions import db
from app.models.user import User
from app.models.notification import Notification
from app.models.device_token import DeviceToken
from app.services.notification_service import send_notification


# Creates a valid citizen account for notification service tests.
@pytest.fixture()
def test_user(app):
    with app.app_context():
        user = User(
            name="Test Citizen",
            email="notification_test@example.com"
        )
        user.set_password("TestPassword123")

        db.session.add(user)
        db.session.commit()

        user_id = user.id

        yield user_id


# Tests that a notification is saved when the user has no active devices.
def test_notification_saved_when_no_devices(app, test_user):
    with app.app_context():
        notification = send_notification(
            user_id=test_user,
            title="Flood Alert",
            message="High flood risk detected in your area.",
            risk_level="high"
        )

        saved_notification = db.session.get(
            Notification,
            notification.id
        )

        assert saved_notification is not None
        assert saved_notification.delivery_status == "no_devices"
        assert saved_notification.risk_level == "high"


# Tests successful delivery to a registered device using mocked Firebase.
def test_notification_sent_successfully(app, test_user, monkeypatch):
    with app.app_context():
        device = DeviceToken(
            user_id=test_user,
            fid="test-firebase-installation-id",
            platform="android",
            is_active=True
        )
        db.session.add(device)
        db.session.commit()

        # Pretend Firebase has already been initialized.
        monkeypatch.setattr(
            "app.services.notification_service.firebase_admin.get_app",
            lambda: object()
        )

        # Pretend Firebase successfully accepts the message.
        monkeypatch.setattr(
            "app.services.notification_service.messaging.send",
            lambda message, app=None: "mock-message-id"
        )

        notification = send_notification(
            user_id=test_user,
            title="Flood Alert",
            message="Severe flood risk detected.",
            risk_level="severe"
        )

        assert notification.delivery_status == "sent"


# Tests that Firebase-invalid device tokens are deactivated.
# Tests that Firebase-invalid device tokens are deactivated.
def test_unregistered_device_token_is_deactivated(
    app,
    test_user,
    monkeypatch
):
    with app.app_context():
        device = DeviceToken(
            user_id=test_user,
            fid="test-firebase-installation-id",
            platform="android",
            is_active=True
        )
        db.session.add(device)
        db.session.commit()

        monkeypatch.setattr(
            "app.services.notification_service.firebase_admin.get_app",
            lambda: object()
        )

        # Simulates Firebase reporting that the device token is unregistered.
        def raise_unregistered(message, app=None):
            raise messaging.UnregisteredError("Device token is unregistered")

        monkeypatch.setattr(
            "app.services.notification_service.messaging.send",
            raise_unregistered
        )

        notification = send_notification(
            user_id=test_user,
            title="Flood Alert",
            message="High flood risk detected.",
            risk_level="high"
        )

        saved_device = db.session.get(DeviceToken, device.id)

        assert saved_device.is_active is False
        assert notification.delivery_status == "failed"

# Tests that notifications remain pending if Firebase is not initialized.
def test_notification_remains_pending_without_firebase(app, test_user, monkeypatch):
    with app.app_context():
        device = DeviceToken(
            user_id=test_user,
            fid="test-firebase-installation-id",
            platform="android",
            is_active=True
        )
        db.session.add(device)
        db.session.commit()

        def firebase_not_initialized():
            raise ValueError("Firebase application is not initialized")

        monkeypatch.setattr(
            "app.services.notification_service.firebase_admin.get_app",
            firebase_not_initialized
        )

        notification = send_notification(
            user_id=test_user,
            title="Flood Alert",
            message="Flood risk assessment completed."
        )

        assert notification.delivery_status == "pending"


# Tests that invalid notification data is rejected.
@pytest.mark.parametrize(
    "notification_data",
    [
        {"title": "", "message": "Flood alert"},
        {"title": "Flood alert", "message": ""},
        {"title": "Flood alert", "message": "Risk detected", "risk_level": "extreme"},
        {"title": "Flood alert", "message": "Risk detected", "latitude": 100},
        {"title": "Flood alert", "message": "Risk detected", "longitude": 200},
    ]
)
def test_invalid_notification_data_is_rejected(
    app,
    test_user,
    notification_data
):
    with app.app_context():
        with pytest.raises(ValueError):
            send_notification(
                user_id=test_user,
                **notification_data
            )


# Tests that sending a notification for a nonexistent user is rejected.
def test_notification_rejects_nonexistent_user(app):
    with app.app_context():
        with pytest.raises(ValueError, match="User does not exist"):
            send_notification(
                user_id=999999,
                title="Flood Alert",
                message="Test message"
            )
