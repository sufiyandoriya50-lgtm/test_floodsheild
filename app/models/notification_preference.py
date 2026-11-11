
from sqlalchemy import CheckConstraint

from app.extensions import db


# Stores the notification preferences selected by a FloodShield user.
class NotificationPreference(db.Model):
    __tablename__ = "notification_preferences"

    # Enforce valid Boolean preference values.
    __table_args__ = (
       CheckConstraint(
           "push_enabled IN (TRUE, FALSE)",
           name="check_notification_preference_push"
       ),
       CheckConstraint(
           "high_risk_enabled IN (TRUE, FALSE)",
           name="check_notification_preference_high_risk"
       ),
       CheckConstraint(
           "severe_risk_enabled IN (TRUE, FALSE)",
           name="check_notification_preference_severe_risk"
       ),
    )

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True
    )

    push_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    high_risk_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    severe_risk_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    def __repr__(self):
        return f"<NotificationPreference user={self.user_id}>"
