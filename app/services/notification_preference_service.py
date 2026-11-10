
from app.extensions import db
from app.models.user import User
from app.models.notification_preference import NotificationPreference


# Retrieves a user's notification preferences, creating default preferences when needed.
def get_or_create_preferences(user_id):

    user = db.session.get(User, user_id)

    if user is None:
        raise ValueError("User does not exist")

    preferences = NotificationPreference.query.filter_by(
        user_id=user_id
    ).first()

    if preferences is None:
        preferences = NotificationPreference(user_id=user_id)

        try:
            db.session.add(preferences)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    return preferences


# Updates the notification preferences selected by a user.
def update_notification_preferences(user_id, updates):

    if not isinstance(updates, dict) or not updates:
        raise ValueError("At least one preference must be provided")

    allowed_fields = {
        "push_enabled",
        "high_risk_enabled",
        "severe_risk_enabled"
    }

    invalid_fields = set(updates.keys()) - allowed_fields

    if invalid_fields:
        raise ValueError(
            f"Unsupported preference fields: {', '.join(sorted(invalid_fields))}"
        )

    for field, value in updates.items():
        if not isinstance(value, bool):
            raise ValueError(f"{field} must be true or false")

    preferences = get_or_create_preferences(user_id)

    try:
        for field, value in updates.items():
            setattr(preferences, field, value)

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise

    return preferences
