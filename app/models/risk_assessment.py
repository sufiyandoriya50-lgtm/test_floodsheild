
from datetime import datetime, timezone

from app.extensions import db


class RiskAssessment(db.Model):
    """
    Stores location-specific flood-risk assessments.
    """

    __tablename__ = "risk_assessments"

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Geographic location
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Risk classification
    risk_level = db.Column(
        db.String(20),
        nullable=False
    )

    # Explanation of the assessment
    description = db.Column(db.Text, nullable=True)

    # Assessment timestamp
    assessed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return (
            f"<RiskAssessment {self.id}: "
            f"{self.risk_level}>"
        )
