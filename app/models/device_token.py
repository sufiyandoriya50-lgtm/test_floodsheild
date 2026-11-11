
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint

from app.extensions import db


# Represents a mobile device registered to receive FloodShield push notifications.
class DeviceToken(db.Model):
    __tablename__ = "device_tokens"

    # Enforce valid device identifiers and supported platforms.
    __table_args__ = (
        CheckConstraint(
            "platform IN ('android', 'ios')",
            name="check_device_token_platform"
        ),
        CheckConstraint(
            "("
            "token IS NOT NULL "
            "AND length(trim(token)) > 0 "
            "AND length(token) <= 512"
            ") OR ("
            "fid IS NOT NULL "
            "AND length(trim(fid)) > 0 "
            "AND length(fid) <= 512"
            ")",
            name="check_device_token_identifier"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # FCM registration token used to deliver push notifications.
    token = db.Column(
        db.String(512),
        unique=True,
        nullable=True
    )

    # Legacy Firebase Installation ID retained for compatibility.
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
