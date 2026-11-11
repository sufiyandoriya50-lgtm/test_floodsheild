
import pytest

from app.extensions import db
from app.models.user import User
from app.models.device_token import DeviceToken
from app.services.device_token_service import register_device_token


# Creates or retrieves a citizen account for device-token tests.
def get_device_test_user():
    """Return a persistent test user."""

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

    return user


# Tests that a valid Firebase Installation ID is registered successfully.
def test_register_device_token(app):
    with app.app_context():
        user = get_device_test_user()

        device = register_device_token(
            user_id=user.id,
            fid="test-firebase-installation-id-123",
            platform="android"
        )

        assert device.id is not None
        assert device.user_id == user.id
        assert device.fid == "test-firebase-installation-id-123"
        assert device.token is None
        assert device.platform == "android"
        assert device.is_active is True


# Tests that an existing FID can be reactivated by its owner.
def test_update_existing_device_token(app):
    with app.app_context():
        user = get_device_test_user()

        device = DeviceToken(
            user_id=user.id,
            fid="test-update-firebase-installation-id",
            platform="android",
            is_active=False
        )

        db.session.add(device)
        db.session.commit()

        updated_device = register_device_token(
            user_id=user.id,
            fid="test-update-firebase-installation-id",
            platform="ios"
        )

        assert updated_device.id == device.id
        assert updated_device.platform == "ios"
        assert updated_device.is_active is True



# Tests that a device cannot be registered to another user's account.
def test_reject_device_token_owned_by_another_user(app):
    with app.app_context():
        first_user = get_device_test_user()
        first_user_id = first_user.id

        second_user = User(
            name="Second Device User",
            email="second_device_test@example.com"
        )
        second_user.set_password("SecondDevicePassword123!")

        db.session.add(second_user)
        db.session.commit()

        second_user_id = second_user.id

        # Register the FID to the first user.
        register_device_token(
            user_id=first_user_id,
            fid="test-firebase-installation-id-123",
            platform="android"
        )

        # Another user must not be allowed to claim the same FID.
        with pytest.raises(ValueError, match="already registered"):
            register_device_token(
                user_id=second_user_id,
                fid="test-firebase-installation-id-123",
                platform="android"
            )

        device = DeviceToken.query.filter_by(
            fid="test-firebase-installation-id-123"
        ).first()

        assert device is not None
        assert device.user_id == first_user_id
# Tests that invalid platforms are rejected.
def test_reject_invalid_device_platform(app):
    with app.app_context():
        user = get_device_test_user()

        with pytest.raises(ValueError):
            register_device_token(
                user_id=user.id,
                fid="another-test-firebase-installation-id",
                platform="windows"
            )
# Tests that user representations do not expose personal information.
def test_user_repr_does_not_expose_personal_information(app):
    with app.app_context():
        user = get_device_test_user()

        user.phone_number = "privacy-test-123"
        db.session.commit()

        user_representation = repr(user)

        assert str(user.id) in user_representation
        assert user.role in user_representation

        assert user.email not in user_representation
        assert user.phone_number not in user_representation
        assert user.password_hash not in user_representation
        assert (
            user.firebase_uid is None
            or user.firebase_uid not in user_representation
             )