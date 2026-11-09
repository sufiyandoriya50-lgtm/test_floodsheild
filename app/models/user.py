
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(db.Model):
    """
    Represents a registered FloodShield user.
    """

    __tablename__ = "users"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # User information
    name = db.Column(db.String(100), nullable=False)

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    # Store password hash, never the original password
    password_hash = db.Column(db.String(256), nullable=False)
    # Defines whether the account is a normal citizen or an administrator.
    role = db.Column(
           db.String(20),
           nullable=False,
           default="citizen",
           server_default="citizen"
           )

    # Account creation timestamp (UTC)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def set_password(self, password):
        """Generate and store a secure password hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check whether the supplied password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
   
    def __repr__(self):
        return f"<User {self.email}>"
