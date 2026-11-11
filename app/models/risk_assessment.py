
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint

from app.extensions import db


# Stores location-specific flood-risk assessments and enforces data integrity.
class RiskAssessment(db.Model):

    __tablename__ = "risk_assessments"

    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="check_risk_assessment_latitude"
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="check_risk_assessment_longitude"
        ),
        CheckConstraint(
            "risk_level IN "
            "('low', 'moderate', 'high', 'severe', 'insufficient_data')",
            name="check_risk_assessment_level"
        ),
        CheckConstraint(
            "risk_score IS NULL OR "
            "(risk_score >= 0 AND risk_score <= 100)",
            name="check_risk_assessment_score"
        ),
        CheckConstraint(
            "data_completeness IS NULL OR "
            "(data_completeness >= 0 AND data_completeness <= 100)",
            name="check_risk_assessment_completeness"
        ),
    )

    # Unique database ID for each risk assessment.
    id = db.Column(db.Integer, primary_key=True)

    # Geographic location where flood risk was assessed.
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Final risk classification.
    risk_level = db.Column(db.String(30), nullable=False)

    # Numerical combined risk score, from 0 to 100.
    risk_score = db.Column(db.Float, nullable=True)

    # Stores individual factor results as structured JSON.
    factor_details = db.Column(db.JSON, nullable=True)

    # Percentage of weighted risk factors available.
    data_completeness = db.Column(db.Float, nullable=True)

    # Human-readable explanation of the assessment.
    description = db.Column(db.Text, nullable=True)

    # Date and time when the assessment was created.
    assessed_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Provides a readable representation of a risk assessment.
    def __repr__(self):
        return (
            f"<RiskAssessment {self.id}: "
            f"{self.risk_level} ({self.risk_score})>"
        )
