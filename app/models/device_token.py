
from datetime import datetime, timezone

from app.extensions import db


# Represents a mobile device registered to receive FloodShield push notifications.
class DeviceToken(db.Model):
    __tablename__ = "device_tokens"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Legacy FCM registration token retained for existing database records.
    token = db.Column(
        db.String(512),
        unique=True,
        nullable=True
    )

    # Firebase Installation ID used for new device registrations.
    fid = db.Column(
        db.String(512),
        unique=True,
        nullable=True
    )

    platform = db.Column(db.String(20), nullable=False)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<DeviceToken {self.id}: user={self.user_id}>"
