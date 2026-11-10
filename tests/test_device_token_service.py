
import pytest

from app.extensions import db
from app.models.user import User
from app.models.device_token import DeviceToken
from app.services.device_token_service import register_device_token


# Tests that a valid Firebase Installation ID is registered successfully.
def test_register_device_token(app):
    with app.app_context():
        user = User.query.filter_by(
            email="device_test@example.com"
        ).first()

        if user is None:
            user = User(
                name="Device Test User",
                email="device_test@example.com"
            )
            user.set_password("DeviceTestPassword123!")
            db.session.add(user)
            db.session.commit()

        device = register_device_token(
            user_id=user.id,
            fid="test-firebase-device-token-123",
            platform="android"
        )

        assert device.id is not None
        assert device.user_id == user.id
        assert device.fid == "test-firebase-device-token-123"
        assert device.platform == "android"
        assert device.is_active is True


# Tests that invalid platforms are rejected.
def test_reject_invalid_device_platform(app):
    with app.app_context():
        user = User.query.filter_by(
            email="device_test@example.com"
        ).first()

        if user is None:
            user = User(
                name="Device Test User",
                email="device_test@example.com"
            )
            user.set_password("DeviceTestPassword123!")
            db.session.add(user)
            db.session.commit()

        with pytest.raises(ValueError):
            register_device_token(
                user_id=user.id,
                fid="another-test-device-token",
                platform="windows"
            )
