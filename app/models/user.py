
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


# Represents a registered FloodShield citizen or administrator.
class User(db.Model):

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) > 0 AND length(name) <= 100",
            name="check_user_name"
        ),
        CheckConstraint(
            "role IN ('citizen', 'admin')",
            name="check_user_role"
        ),
        CheckConstraint(
            "email IS NULL OR "
            "(length(trim(email)) > 0 AND length(email) <= 120)",
            name="check_user_email"
        ),
        CheckConstraint(
            "password_hash IS NULL OR "
            "length(trim(password_hash)) > 0",
            name="check_user_password_hash"
        ),
        CheckConstraint(
            "firebase_uid IS NULL OR "
            "(length(trim(firebase_uid)) > 0 AND length(firebase_uid) <= 128)",
            name="check_user_firebase_uid"
        ),
        CheckConstraint(
            "phone_number IS NULL OR "
            "(length(trim(phone_number)) > 0 AND length(phone_number) <= 20)",
            name="check_user_phone_number"
        ),
    )

    # Primary key.
    id = db.Column(db.Integer, primary_key=True)

    # Basic user information.
    name = db.Column(db.String(100), nullable=False)

    # Email is optional for phone-authenticated citizens.
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=True,
        index=True
    )

    # Password is optional for phone-authenticated citizens.
    password_hash = db.Column(
        db.String(256),
        nullable=True
    )

    # Firebase authentication identity.
    firebase_uid = db.Column(
        db.String(128),
        unique=True,
        nullable=True
    )

    # Phone number associated with Firebase authentication.
    phone_number = db.Column(
        db.String(20),
        unique=True,
        nullable=True
    )

    # Defines citizen or administrator privileges.
    role = db.Column(
        db.String(20),
        nullable=False,
        default="citizen",
        server_default="citizen"
    )

    # Account creation timestamp (UTC).
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Generates and stores a secure password hash.
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Checks a password without exposing the stored password hash.
    def check_password(self, password):

        if not self.password_hash or not isinstance(password, str):
            return False

        return check_password_hash(self.password_hash, password)
    # Provides a privacy-safe representation of the user.
    def __repr__(self):
        return f"<User id={self.id} role={self.role}>"