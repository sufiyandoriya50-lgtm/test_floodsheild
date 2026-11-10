
import pytest

from app.extensions import db
from app.models.user import User
from app.models.notification_preference import NotificationPreference
from app.services.notification_preference_service import (
    get_or_create_preferences,
    update_notification_preferences,
)


# Creates a real test user for notification preference tests.
@pytest.fixture
def preference_user(app):
    with app.app_context():
        user = User(
            name="Preference Test User",
            email="preferences@example.com",
        )
        user.set_password("test-password-123")
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        yield user_id


# Tests that a new user receives the default notification settings.
def test_create_default_preferences(app, preference_user):
    with app.app_context():
        preferences = get_or_create_preferences(preference_user)

        assert preferences.user_id == preference_user
        assert preferences.push_enabled is True
        assert preferences.high_risk_enabled is True
        assert preferences.severe_risk_enabled is True


# Tests that retrieving preferences does not create duplicate records.
def test_get_existing_preferences_without_duplicates(app, preference_user):
    with app.app_context():
        first = get_or_create_preferences(preference_user)
        second = get_or_create_preferences(preference_user)

        assert first.id == second.id

        count = NotificationPreference.query.filter_by(
            user_id=preference_user
        ).count()

        assert count == 1


# Tests that valid preference changes are saved correctly.
def test_update_notification_preferences(app, preference_user):
    with app.app_context():
        preferences = update_notification_preferences(
            preference_user,
            {
                "high_risk_enabled": False,
                "severe_risk_enabled": True,
            },
        )

        assert preferences.high_risk_enabled is False
        assert preferences.severe_risk_enabled is True
        assert preferences.push_enabled is True


# Tests that unknown preference fields are rejected.
def test_reject_unknown_preference_field(app, preference_user):
    with app.app_context():
        with pytest.raises(ValueError):
            update_notification_preferences(
                preference_user,
                {"unknown_setting": False},
            )


# Tests that non-boolean preference values are rejected.
@pytest.mark.parametrize("invalid_value", ["yes", 1, None, "false"])
def test_reject_non_boolean_preference_values(
    app, preference_user, invalid_value
):
    with app.app_context():
        with pytest.raises(ValueError):
            update_notification_preferences(
                preference_user,
                {"high_risk_enabled": invalid_value},
            )


# Tests that an empty update request is rejected.
def test_reject_empty_preference_update(app, preference_user):
    with app.app_context():
        with pytest.raises(ValueError):
            update_notification_preferences(preference_user, {})


# Tests that preferences cannot be created for a nonexistent user.
def test_reject_nonexistent_user(app):
    with app.app_context():
        with pytest.raises(ValueError, match="User does not exist"):
            get_or_create_preferences(999999)
