
from app.extensions import db


# Stores the notification preferences selected by a FloodShield user.
class NotificationPreference(db.Model):
    __tablename__ = "notification_preferences"

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
