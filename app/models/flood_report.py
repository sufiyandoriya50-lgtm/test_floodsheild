
from datetime import datetime, timezone

from app.extensions import db


class FloodReport(db.Model):
    """
    Represents a community-submitted flood or waterlogging report.
    """

    __tablename__ = "flood_reports"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # User who submitted the report
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # Geographic coordinates
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Report information
    water_depth_cm = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Verification status
    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )

    # Report submission time
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationship with User model
    user = db.relationship(
        "User",
        backref=db.backref("flood_reports", lazy=True)
    )

    def __repr__(self):
        return f"<FloodReport {self.id}: {self.status}>"
